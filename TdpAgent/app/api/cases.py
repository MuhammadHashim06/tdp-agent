from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Optional, Any, Dict

from pydantic import BaseModel, Field

from app.core.types import CaseCreate, CaseUpdate
from app.core.status_rules import normalize_status
from app.mysql_ops import MysqlOps

from app.ai.tasks import draft_case_acceptance
from app.graph.reply import create_reply_draft, update_draft_message, send_draft_message
import html

router = APIRouter()


# ---------------------------
# Models
# ---------------------------
class StaffingConfirmIn(BaseModel):
    therapist_name: Optional[str] = None
    discipline: Optional[str] = None
    availability: Optional[str] = None

    # Accept both referral_email and referral_source_email
    referral_email: Optional[str] = Field(default=None, alias="referral_source_email")

    class Config:
        populate_by_name = True


class AcceptanceDraftOut(BaseModel):
    case_id: int
    draft_id: int
    email_id: int
    model: str
    graph_draft_message_id: Optional[str] = None
    graph_draft_web_link: Optional[str] = None
    idempotent: bool = False


class AcceptanceSendOut(BaseModel):
    ok: bool
    case_id: int
    draft_id: int
    email_id: int
    mailbox: str
    status: str


# Manual update endpoint (Stage 3/4/6)
class CasePatchIn(BaseModel):
    status: Optional[str] = None
    note: Optional[str] = None
    actor: str = "human"


# ---------------------------
# Helpers
# ---------------------------
def _strip_subject_header(draft_text: str) -> str:
    if not draft_text:
        return ""
    lines = draft_text.splitlines()
    if lines and lines[0].strip().lower().startswith("subject:"):
        lines = lines[1:]
        if lines and lines[0].strip() == "":
            lines = lines[1:]
    return "\n".join(lines).strip()


def _text_to_simple_html(text: str) -> str:
    text = (text or "").strip()
    escaped = html.escape(text)
    return "<div>" + escaped.replace("\n", "<br>") + "</div>"


def _as_dict(x: Any) -> Dict[str, Any]:
    if isinstance(x, dict):
        return x
    return {}


# ---------------------------
# Core endpoints
# ---------------------------
@router.get("/")
def list_cases(limit: int = 50):
    ops = MysqlOps()
    rows = ops.list_cases()[:limit]
    return {
        "items": [
            {
                "id": r.id,
                "external_id": r.external_id,
                "title": r.title,
                "status": r.status,
                "metadata": r.metadata_json,
            }
            for r in rows
        ]
    }


@router.get("/{case_id}")
def get_case(case_id: int):
    ops = MysqlOps()
    c = ops.get_case_by_id(case_id)
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")

    return {
        "id": c.id,
        "external_id": c.external_id,
        "title": c.title,
        "status": c.status,
        "metadata": c.metadata_json,
    }


@router.get("/{case_id}/timeline")
def case_timeline(case_id: int, limit: int = 200):
    ops = MysqlOps()
    emails = ops.list_emails_for_case(case_id, limit=limit)

    items = []
    for e in emails:
        atts = ops.list_attachments_for_email(e.id)
        items.append(
            {
                "id": e.id,
                "subject": e.subject,
                "sender": e.sender,
                "received_datetime": e.received_datetime,
                "body_preview": e.body_preview,
                "mailbox": getattr(e, "mailbox", None),
                "conversation_id": e.conversation_id,
                "has_attachments": len(atts) > 0,
                "attachments": [
                    {
                        "id": a.id,
                        "attachment_id": a.attachment_id,
                        "name": a.name,
                        "content_type": a.content_type,
                        "size": a.size,
                        "is_inline": bool(a.is_inline),
                        "content_id": a.content_id,
                        "local_path": a.local_path,
                    }
                    for a in atts
                ],
            }
        )

    return {"case_id": case_id, "count": len(items), "items": items}


@router.post("/")
def create_case(payload: CaseCreate):
    ops = MysqlOps()
    case_id = ops.create_case(
        external_id=payload.external_id,
        title=payload.title,
        status=normalize_status(payload.status),
        metadata=payload.metadata,
    )
    return {"id": case_id}


@router.patch("/{case_id}")
def update_case(case_id: int, payload: CaseUpdate):
    """
    Existing patch endpoint (kept).
    - Title/status are direct updates
    - Metadata is merged
    """
    ops = MysqlOps()

    fields = {}
    if payload.title is not None:
        fields["title"] = payload.title
    if payload.status is not None:
        fields["status"] = normalize_status(payload.status)

    if payload.metadata is not None:
        if not isinstance(payload.metadata, dict):
            raise HTTPException(status_code=400, detail="metadata must be an object")
        ops.merge_case_metadata(case_id, payload.metadata)

    if fields:
        try:
            ops.update_case(case_id, fields)
        except ValueError:
            raise HTTPException(status_code=404, detail="Case not found")
    elif payload.metadata is None:
        raise HTTPException(status_code=400, detail="No fields to update")

    return {"ok": True}


@router.patch("/{case_id}/manual")
def patch_case_manual(case_id: int, body: CasePatchIn):
    """
    Stage 3/4/6 manual update API:
    - Set status (normalized)
    - Logs a status_updated event for audit trail
    """
    ops = MysqlOps()
    c = ops.get_case_by_id(case_id)
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")

    if body.status is None:
        raise HTTPException(status_code=400, detail="status is required")

    new_status = normalize_status(body.status)
    old_status = c.status

    ops.update_case(case_id, {"status": new_status})

    # Dedup is not necessary here; manual clicks can be repeated intentionally.
    ops.create_case_event(
        case_id=case_id,
        email_id=None,
        event_type="status_updated",
        actor=(body.actor or "human"),
        payload={"old_status": old_status, "new_status": new_status, "note": body.note},
    )

    return {"ok": True, "case_id": case_id, "status": new_status}


# ---------------------------
# Stage 2: Staffing confirm (explicit transition)
# ---------------------------
@router.post("/{case_id}/staffing/confirm")
def confirm_staffing(case_id: int, body: StaffingConfirmIn):
    ops = MysqlOps()
    c = ops.get_case_by_id(case_id)
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")

    current = (c.status or "").strip().lower()
    if current in {"closed"}:
        raise HTTPException(status_code=400, detail=f"Cannot confirm staffing from status '{c.status}'")

    payload = {
        "therapist_name": body.therapist_name,
        "discipline": body.discipline,
        "availability": body.availability,
        "referral_email": body.referral_email,
    }

    ops.merge_case_metadata(case_id, {"staffing": payload})

    # Idempotent event logging
    if not ops.case_event_exists_any(case_id=case_id, email_id=None, event_type="staffed"):
        ops.create_case_event(
            case_id=case_id,
            email_id=None,
            event_type="staffed",
            actor="human",
            payload=payload,
        )

    # Transition to staffed (idempotent)
    ops.update_case(case_id, {"status": "staffed"})
    return {"ok": True, "case_id": case_id, "status": "staffed"}


# ---------------------------
# Stage 3: Acceptance draft (idempotent)
# ---------------------------
@router.post("/{case_id}/drafts/acceptance", response_model=AcceptanceDraftOut)
def create_acceptance_draft(case_id: int):
    ops = MysqlOps()
    c = ops.get_case_by_id(case_id)
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")

    current = (c.status or "").strip().lower()
    if current not in {"staffed", "acceptance drafted"}:
        raise HTTPException(status_code=400, detail="Case must be 'staffed' before drafting acceptance")

    # If you already created an acceptance draft earlier (even if status is wrong),
    # return the latest unsent one for this case.
    existing = None
    try:
        existing = ops.get_latest_unsent_draft_for_case_kind(case_id=case_id, kind="acceptance")
    except Exception:
        existing = None

    if existing:
        # Ensure status stays consistent
        if (c.status or "").strip().lower() != "acceptance drafted":
            ops.update_case(case_id, {"status": "acceptance drafted"})

        return AcceptanceDraftOut(
            case_id=case_id,
            draft_id=int(existing.id),
            email_id=int(existing.email_id),
            model=str(existing.model),
            graph_draft_message_id=getattr(existing, "graph_draft_message_id", None),
            graph_draft_web_link=getattr(existing, "graph_draft_web_link", None),
            idempotent=True,
        )

    meta = _as_dict(c.metadata_json)
    staffing = _as_dict(meta.get("staffing"))

    if not staffing:
        raise HTTPException(
            status_code=400,
            detail="Staffing has not been confirmed yet. Call /staffing/confirm first.",
        )

    referral_email = staffing.get("referral_email")
    therapist_name = staffing.get("therapist_name")
    discipline = staffing.get("discipline")
    availability = staffing.get("availability")

    # Use seed email if present, else latest email in thread
    seed_email_id = meta.get("seed_email_id")
    email_id = int(seed_email_id) if seed_email_id else None
    if not email_id:
        latest = ops.get_latest_email_for_case(case_id)
        if latest:
            email_id = int(latest.id)

    if not email_id:
        raise HTTPException(status_code=400, detail="No email found to attach the draft to")

    email_row = ops.get_email_by_id(int(email_id))
    if not email_row:
        raise HTTPException(status_code=404, detail="Seed email not found")

    mailbox = (email_row.mailbox or "").strip()
    message_id = (email_row.message_id or "").strip()

    if not mailbox:
        raise HTTPException(status_code=400, detail="Seed email mailbox missing")
    if not message_id:
        raise HTTPException(status_code=400, detail="Seed email message_id missing")

    # Generate acceptance text (LLM)
    draft_text, model = draft_case_acceptance(
        case_title=c.title,
        referral_source_email=referral_email,
        therapist_name=therapist_name,
        discipline=discipline,
        availability=availability,
    )

    # Create Graph reply draft
    graph_draft = create_reply_draft(mailbox=mailbox, message_id=message_id)
    graph_draft_id = (graph_draft.get("id") or "").strip()
    graph_weblink = (graph_draft.get("webLink") or "").strip() if isinstance(graph_draft.get("webLink"), str) else None

    if not graph_draft_id:
        raise HTTPException(status_code=502, detail="Graph did not return draft id")

    body_text = _strip_subject_header(draft_text or "")
    body_html = _text_to_simple_html(body_text)

    # If referral_email is provided, force To to that email; otherwise keep default reply recipients
    to_list = [referral_email] if referral_email else None

    update_draft_message(
        mailbox=mailbox,
        draft_message_id=graph_draft_id,
        body_html=body_html,
        to_recipients=to_list,
    )

    # Store in DB (kind="acceptance" so we can find it later reliably)
    draft_id = ops.create_draft(
        email_id=int(email_id),
        draft=draft_text,
        model=model,
        tone="professional",
        mailbox=mailbox,
        graph_draft_message_id=graph_draft_id,
        graph_draft_web_link=graph_weblink,
        kind="acceptance",
        requires_approval=1,
    )

    # Update case status
    ops.update_case(case_id, {"status": "acceptance drafted"})

    # Log event once per email
    if not ops.case_event_exists_any(case_id=case_id, email_id=int(email_id), event_type="acceptance_draft_created"):
        ops.create_case_event(
            case_id=case_id,
            email_id=int(email_id),
            event_type="acceptance_draft_created",
            actor="ai",
            payload={
                "referral_email": referral_email,
                "draft_id": int(draft_id),
                "graph_draft_message_id": graph_draft_id,
                "graph_draft_web_link": graph_weblink,
            },
        )

    return AcceptanceDraftOut(
        case_id=case_id,
        draft_id=int(draft_id),
        email_id=int(email_id),
        model=model,
        graph_draft_message_id=graph_draft_id,
        graph_draft_web_link=graph_weblink,
        idempotent=False,
    )


@router.post("/{case_id}/drafts/acceptance/send", response_model=AcceptanceSendOut)
def send_acceptance_draft(case_id: int):
    ops = MysqlOps()
    c = ops.get_case_by_id(case_id)
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")

    current = (c.status or "").strip().lower()
    if current != "acceptance drafted":
        raise HTTPException(status_code=400, detail="Case must be in 'acceptance drafted' status before sending")

    # Send the latest unsent acceptance draft for this case (NOT "latest draft for seed email")
    d = None
    try:
        d = ops.get_latest_unsent_draft_for_case_kind(case_id=case_id, kind="acceptance")
    except Exception:
        d = None

    if not d:
        raise HTTPException(status_code=404, detail="No unsent acceptance draft found for this case")

    if (getattr(d, "status", None) or "draft") == "sent":
        raise HTTPException(status_code=400, detail="Draft already sent")

    mailbox = (getattr(d, "mailbox", None) or "").strip()
    graph_id = (getattr(d, "graph_draft_message_id", None) or "").strip()

    if not mailbox:
        raise HTTPException(status_code=400, detail="Draft mailbox missing (cannot send via Graph)")
    if not graph_id:
        raise HTTPException(status_code=400, detail="Draft graph_draft_message_id missing (cannot send via Graph)")

    try:
        send_draft_message(mailbox=mailbox, draft_message_id=graph_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Graph send failed: {str(e)}")

    # Mark draft sent + case status
    ops.mark_draft_sent(int(d.id), mailbox=mailbox, sent_message_id=None)

    # Keep your existing status string; if you prefer, you can leave as manual later.
    ops.update_case(case_id, {"status": "acceptance sent"})

    if not ops.case_event_exists_any(case_id=case_id, email_id=int(d.email_id), event_type="acceptance_sent"):
        ops.create_case_event(
            case_id=case_id,
            email_id=int(d.email_id),
            event_type="acceptance_sent",
            actor="ai",
            payload={
                "draft_id": int(d.id),
                "mailbox": mailbox,
                "graph_draft_message_id": graph_id,
                "graph_draft_web_link": getattr(d, "graph_draft_web_link", None),
            },
        )

    return AcceptanceSendOut(
        ok=True,
        case_id=case_id,
        draft_id=int(d.id),
        email_id=int(d.email_id),
        mailbox=mailbox,
        status="acceptance sent",
    )
