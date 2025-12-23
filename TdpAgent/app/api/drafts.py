from __future__ import annotations

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from app.mysql_ops import MysqlOps
from app.ai.tasks import draft_reply

import html
from app.graph.reply import create_reply_draft, update_draft_message, send_draft_message

router = APIRouter()


class DraftCreateIn(BaseModel):
    tone: str = "professional"
    instructions: Optional[str] = None
    # allow overriding recipients (useful for acceptance drafts, wrong reply-all, etc.)
    to: Optional[List[EmailStr]] = None
    # optional classification for dedupe/lookup
    kind: Optional[str] = None


class DraftUpdateIn(BaseModel):
    # allow updating body + optionally recipients
    draft: str
    to: Optional[List[EmailStr]] = None


class DraftSendOut(BaseModel):
    ok: bool
    draft_id: int
    email_id: int
    mailbox: str
    status: str


def _strip_subject_header(draft_text: str) -> str:
    """
    Draft text often starts with:
      Subject: ...
      <blank line>
      Hello,...

    Graph /reply takes only a comment/body. Strip the Subject line if present.
    """
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

@router.get("/emails")
def get_all_drafts(limit: int = 20):
    """
    Retrieves all email drafts with pagination support.
    """
    ops = MysqlOps()
    rows = ops.list_all_drafts(limit=limit)
    return {
        "items": [
            {
                "id": d.id,
                "model": d.model,
                "tone": d.tone,
                "kind": getattr(d, "kind", None),
                "status": getattr(d, "status", "draft"),
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "sent_at": d.sent_at.isoformat() if getattr(d, "sent_at", None) else None,
                "graph_draft_message_id": getattr(d, "graph_draft_message_id", None),
                "graph_draft_web_link": getattr(d, "graph_draft_web_link", None),
            }
            for d in rows
        ]
    }

@router.post("/emails/{email_id}")
def create_draft(email_id: int, body: DraftCreateIn):
    """
    Creates:
      1) Draft text via LLM
      2) Outlook (Graph) reply draft on the given email thread
      3) Saves draft in DB (including graph ids)

    Optional:
      - body.to forces recipients (Graph To override)
      - body.kind lets you later fetch/dedupe by kind (e.g., "acceptance", "followup")
    """
    ops = MysqlOps()
    email = ops.get_email_by_id(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    draft_text, model = draft_reply(
        subject=email.subject or "",
        sender=email.sender or "",
        body_html=email.body_html,
        body_preview=email.body_preview,
        tone=body.tone,
        instructions=body.instructions,
    )

    mailbox = (getattr(email, "mailbox", None) or "").strip()
    message_id = (getattr(email, "message_id", None) or "").strip()  # Graph message id

    if not mailbox:
        raise HTTPException(status_code=400, detail="Email mailbox missing (cannot create Graph draft)")
    if not message_id:
        raise HTTPException(status_code=400, detail="Email message_id missing (cannot create Graph draft)")

    graph_draft = create_reply_draft(mailbox=mailbox, message_id=message_id)
    graph_draft_id = (graph_draft.get("id") or "").strip()
    graph_weblink = (graph_draft.get("webLink") or "").strip() if isinstance(graph_draft.get("webLink"), str) else None

    if not graph_draft_id:
        raise HTTPException(status_code=502, detail="Graph did not return draft id")

    body_text = _strip_subject_header(draft_text or "")
    body_html = _text_to_simple_html(body_text)

    to_recipients = [str(x) for x in body.to] if body.to else None

    update_draft_message(
        mailbox=mailbox,
        draft_message_id=graph_draft_id,
        body_html=body_html,
        to_recipients=to_recipients,  # None keeps default reply recipients
    )

    # Save draft in DB (expects your MysqlOps.create_draft supports graph fields + kind)
    try:
        draft_id = ops.create_draft(
            email_id=email_id,
            draft=draft_text,
            model=model,
            tone=body.tone,
            mailbox=mailbox,
            graph_draft_message_id=graph_draft_id,
            graph_draft_web_link=graph_weblink,
            kind=body.kind,
        )
    except TypeError:
        # Backward compatible if create_draft doesn't support new params yet
        draft_id = ops.create_draft(
            email_id=email_id,
            draft=draft_text,
            model=model,
            tone=body.tone,
            mailbox=mailbox,
        )

    return {
        "draft_id": draft_id,
        "email_id": email_id,
        "model": model,
        "graph_draft_message_id": graph_draft_id,
        "graph_draft_web_link": graph_weblink,
    }


@router.get("/emails/{email_id}")
def list_email_drafts(email_id: int, limit: int = 20):
    ops = MysqlOps()
    rows = ops.list_drafts_for_email(email_id=email_id, limit=limit)
    return {
        "items": [
            {
                "id": d.id,
                "model": d.model,
                "tone": d.tone,
                "kind": getattr(d, "kind", None),
                "status": getattr(d, "status", "draft"),
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "sent_at": d.sent_at.isoformat() if getattr(d, "sent_at", None) else None,
                "graph_draft_message_id": getattr(d, "graph_draft_message_id", None),
                "graph_draft_web_link": getattr(d, "graph_draft_web_link", None),
            }
            for d in rows
        ]
    }


@router.get("/{draft_id}")
def get_draft(draft_id: int):
    ops = MysqlOps()
    d = ops.get_draft_by_id(draft_id)
    if not d:
        raise HTTPException(status_code=404, detail="Draft not found")

    return {
        "id": d.id,
        "email_id": d.email_id,
        "draft": d.draft,
        "model": d.model,
        "tone": d.tone,
        "kind": getattr(d, "kind", None),
        "status": getattr(d, "status", "draft"),
        "mailbox": getattr(d, "mailbox", None),
        "graph_draft_message_id": getattr(d, "graph_draft_message_id", None),
        "graph_draft_web_link": getattr(d, "graph_draft_web_link", None),
        "sent_message_id": getattr(d, "sent_message_id", None),
        "sent_at": d.sent_at.isoformat() if getattr(d, "sent_at", None) else None,
        "created_at": d.created_at.isoformat() if d.created_at else None,        
    }


@router.put("/{draft_id}")
def update_draft(draft_id: int, body: DraftUpdateIn):
    """
    Updates:
      - DB draft text
      - Graph draft body
      - Optional Graph To recipients override

    This is needed because you can edit draft text in UI and then sync it to Outlook draft.
    """
    ops = MysqlOps()
    d = ops.get_draft_by_id(draft_id)
    if not d:
        raise HTTPException(status_code=404, detail="Draft not found")

    if (getattr(d, "status", "draft") or "draft") == "sent":
        raise HTTPException(status_code=400, detail="Cannot update a sent draft")

    mailbox = (getattr(d, "mailbox", None) or "").strip()
    graph_id = (getattr(d, "graph_draft_message_id", None) or "").strip()

    if not mailbox:
        raise HTTPException(status_code=400, detail="Draft mailbox missing (cannot update Graph draft)")
    if not graph_id:
        raise HTTPException(status_code=400, detail="Draft has no graph_draft_message_id (cannot update Graph draft)")

    body_text = _strip_subject_header(body.draft or "")
    body_html = _text_to_simple_html(body_text)
    to_recipients = [str(x) for x in body.to] if body.to else None

    try:
        update_draft_message(
            mailbox=mailbox,
            draft_message_id=graph_id,
            body_html=body_html,
            to_recipients=to_recipients,  # None keeps whatever Graph already has
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Graph update failed: {str(e)}")

    # Update DB draft text (requires one of these ops methods)
    if hasattr(ops, "update_draft_text"):
        ops.update_draft_text(draft_id=draft_id, draft=body.draft)
    elif hasattr(ops, "update_draft"):
        ops.update_draft(draft_id=draft_id, fields={"draft": body.draft})
    else:
        raise HTTPException(
            status_code=500,
            detail="DB update method missing (need ops.update_draft_text or ops.update_draft)",
        )

    return {"ok": True, "draft_id": draft_id}


@router.post("/{draft_id}/send", response_model=DraftSendOut)
def send_draft(draft_id: int):
    ops = MysqlOps()
    d = ops.get_draft_by_id(draft_id)
    if not d:
        raise HTTPException(status_code=404, detail="Draft not found")

    if (getattr(d, "status", None) or "draft") == "sent":
        raise HTTPException(status_code=400, detail="Draft already sent")

    mailbox = (getattr(d, "mailbox", None) or "").strip()
    graph_id = (getattr(d, "graph_draft_message_id", None) or "").strip()

    if not mailbox:
        raise HTTPException(status_code=400, detail="Draft mailbox missing (cannot send)")
    if not graph_id:
        raise HTTPException(status_code=400, detail="Draft has no graph_draft_message_id (cannot send)")

    try:
        send_draft_message(mailbox=mailbox, draft_message_id=graph_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Graph send failed: {str(e)}")

    ops.mark_draft_sent(draft_id, mailbox=mailbox, sent_message_id=None)

    return DraftSendOut(
        ok=True,
        draft_id=draft_id,
        email_id=int(d.email_id),
        mailbox=mailbox,
        status="sent",
    )
