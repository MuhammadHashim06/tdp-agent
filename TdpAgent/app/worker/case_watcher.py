from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from app.mysql_ops import MysqlOps
from app.core.audit import audit_print
from app.ai.tasks import draft_reply
from app.graph.reply import create_reply_draft, update_draft_message
import html


# ---------------------------
# SLA thresholds (hours)
# ---------------------------
SLA_PENDING_STAFFING_HOURS = float(os.getenv("SLA_PENDING_STAFFING_HOURS", "48"))
SLA_STAFFED_NO_ACCEPTANCE_DRAFT_HOURS = float(os.getenv("SLA_STAFFED_NO_ACCEPTANCE_DRAFT_HOURS", "24"))
SLA_ACCEPTANCE_DRAFTED_NOT_SENT_HOURS = float(os.getenv("SLA_ACCEPTANCE_DRAFTED_NOT_SENT_HOURS", "24"))
SLA_EVAL_DONE_NO_AUTH_HOURS = float(os.getenv("SLA_EVAL_DONE_NO_AUTH_HOURS", "72"))
SLA_AUTH_PENDING_HOURS = float(os.getenv("SLA_AUTH_PENDING_HOURS", "168"))  # 7 days

# Prevent spamming repeated stall events/drafts (fallback)
STALL_RENOTIFY_HOURS = float(os.getenv("STALL_RENOTIFY_HOURS", "12"))

# If you want watcher to only log and not create drafts:
WATCHER_CREATE_DRAFTS = (os.getenv("WATCHER_CREATE_DRAFTS", "1").strip() == "1")


def _as_utc_aware(dt: Optional[datetime]) -> Optional[datetime]:
    if not dt:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _hours_since(dt: Optional[datetime]) -> Optional[float]:
    dt = _as_utc_aware(dt)
    if not dt:
        return None
    delta = _utcnow() - dt
    return delta.total_seconds() / 3600.0


def _text_to_simple_html(text: str) -> str:
    text = (text or "").strip()
    escaped = html.escape(text)
    return "<div>" + escaped.replace("\n", "<br>") + "</div>"


def _strip_subject_header(draft_text: str) -> str:
    if not draft_text:
        return ""
    lines = draft_text.splitlines()
    if lines and lines[0].strip().lower().startswith("subject:"):
        lines = lines[1:]
        if lines and lines[0].strip() == "":
            lines = lines[1:]
    return "\n".join(lines).strip()


def _stall_rule(status: str, hours_idle: float) -> Optional[dict]:
    s = (status or "").strip().lower()

    if s == "pending staffing" and hours_idle >= SLA_PENDING_STAFFING_HOURS:
        return {"stall_type": "pending_staffing_overdue", "threshold_hours": SLA_PENDING_STAFFING_HOURS}

    if s == "staffed" and hours_idle >= SLA_STAFFED_NO_ACCEPTANCE_DRAFT_HOURS:
        return {"stall_type": "staffed_no_acceptance_draft", "threshold_hours": SLA_STAFFED_NO_ACCEPTANCE_DRAFT_HOURS}

    if s == "acceptance drafted" and hours_idle >= SLA_ACCEPTANCE_DRAFTED_NOT_SENT_HOURS:
        return {"stall_type": "acceptance_draft_not_sent", "threshold_hours": SLA_ACCEPTANCE_DRAFTED_NOT_SENT_HOURS}

    if s == "evaluation completed" and hours_idle >= SLA_EVAL_DONE_NO_AUTH_HOURS:
        return {"stall_type": "eval_done_no_auth", "threshold_hours": SLA_EVAL_DONE_NO_AUTH_HOURS}

    if s == "authorization pending" and hours_idle >= SLA_AUTH_PENDING_HOURS:
        return {"stall_type": "auth_pending_overdue", "threshold_hours": SLA_AUTH_PENDING_HOURS}

    return None


def _should_renotify(ops: MysqlOps, case_id: int, stall_type: str) -> bool:
    """
    Time-based safety net. Primary dedupe is stall_key (payload).
    """
    last = ops.get_latest_stall_event(case_id, stall_type)
    if not last or not getattr(last, "created_at", None):
        return True
    h = _hours_since(last.created_at)
    return (h is None) or (h >= STALL_RENOTIFY_HOURS)


def _build_followup_instructions(stall_type: str, case_title: str) -> str:
    base = f"Context: This is a follow-up about case '{case_title}'.\n"

    if stall_type == "pending_staffing_overdue":
        return base + (
            "Write an internal follow-up asking staffing to confirm therapist assignment/availability and next action. "
            "Ask 1-2 direct questions. Keep it short."
        )

    if stall_type == "staffed_no_acceptance_draft":
        return base + (
            "Write a follow-up asking the team to draft the acceptance email and confirm referral contact details. "
            "Keep it short."
        )

    if stall_type == "acceptance_draft_not_sent":
        return base + (
            "Write a follow-up reminding that the acceptance draft is ready and needs review/sending. "
            "Do not claim it was sent. Keep it short."
        )

    if stall_type == "eval_done_no_auth":
        return base + (
            "Write a follow-up asking about authorization next steps and whether any documents are missing. "
            "Keep it short and operational."
        )

    if stall_type == "auth_pending_overdue":
        return base + (
            "Write a follow-up asking for authorization status update and ETA. "
            "If missing payer/portal details, ask for them. Keep it short."
        )

    return base + "Write a short operational follow-up requesting the next step and ETA."


def _stall_dedupe_key(
    *,
    case_id: int,
    case_status: str,
    stall_type: str,
    threshold_hours: float,
    last_meaningful_event_id: Optional[int],
) -> str:
    """
    Stable key for "same stall instance".

    If no new meaningful event happened, last_meaningful_event_id stays the same,
    so stall_key stays the same -> watcher will not duplicate.
    """
    return (
        f"{case_id}|"
        f"{(case_status or '').strip().lower()}|"
        f"{stall_type}|"
        f"{int(threshold_hours)}|"
        f"evt:{last_meaningful_event_id or 0}"
    )


def _create_graph_reply_followup_draft(
    ops: MysqlOps,
    case_id: int,
    stall_type: str,
    stall_key: str,
) -> Optional[int]:
    """
    Creates a reply draft (Graph) on the latest email in the case thread.
    Stores it in drafts table.

    Idempotent:
      - if we already created a follow-up draft for the same stall_key, do nothing.
    """
    # HARD DEDUPE: already created follow-up draft for same stall_key
    if ops.case_event_exists_payload_key(
        case_id=case_id,
        event_type="followup_draft_created",
        key="stall_key",
        value=stall_key,
    ):
        return None

    latest_email = ops.get_latest_email_for_case(case_id)
    if not latest_email:
        return None

    mailbox = (latest_email.mailbox or "").strip()
    message_id = (latest_email.message_id or "").strip()
    if not mailbox or not message_id:
        return None

    instructions = _build_followup_instructions(stall_type, latest_email.subject or f"Case {case_id}")

    draft_text, model = draft_reply(
        subject=latest_email.subject or "",
        sender=latest_email.sender or "",
        body_html=latest_email.body_html,
        body_preview=latest_email.body_preview,
        tone="professional",
        instructions=instructions,
    )

    graph_draft = create_reply_draft(mailbox=mailbox, message_id=message_id)
    graph_draft_id = (graph_draft.get("id") or "").strip()
    graph_weblink = (graph_draft.get("webLink") or "").strip() if isinstance(graph_draft.get("webLink"), str) else None
    if not graph_draft_id:
        return None

    body_text = _strip_subject_header(draft_text)
    body_html = _text_to_simple_html(body_text)

    update_draft_message(
        mailbox=mailbox,
        draft_message_id=graph_draft_id,
        body_html=body_html,
        to_recipients=None,
    )

    draft_id = ops.create_draft(
        email_id=int(latest_email.id),
        draft=draft_text,
        model=model,
        tone="followup",
        mailbox=mailbox,
        graph_draft_message_id=graph_draft_id,
        graph_draft_web_link=graph_weblink,
        kind="followup",
        requires_approval=1,
    )

    # log followup created (with stall_key for dedupe)
    ops.create_case_event(
        case_id=case_id,
        email_id=int(latest_email.id),
        event_type="followup_draft_created",
        actor="ai",
        payload={
            "stall_type": stall_type,
            "stall_key": stall_key,
            "draft_id": draft_id,
            "mailbox": mailbox,
            "graph_draft_message_id": graph_draft_id,
            "graph_draft_web_link": graph_weblink,
        },
    )

    return draft_id


def run_once() -> dict:
    ops = MysqlOps()
    cases = ops.list_active_cases(limit=int(os.getenv("WATCHER_CASE_LIMIT", "500")))

    scanned = 0
    stalled = 0
    stalls_logged = 0
    drafts_created = 0

    for c in cases:
        scanned += 1

        # Use latest meaningful event; if none, fallback to case.updated_at
        last_evt = ops.get_latest_meaningful_event(int(c.id))
        last_dt = last_evt.created_at if (last_evt and getattr(last_evt, "created_at", None)) else c.updated_at
        hours_idle = _hours_since(last_dt)
        if hours_idle is None:
            continue

        rule = _stall_rule(c.status, hours_idle)
        if not rule:
            continue

        stall_type = rule["stall_type"]
        threshold_hours = float(rule["threshold_hours"])
        last_meaningful_event_id = int(getattr(last_evt, "id", 0) or 0) if last_evt else 0

        stall_key = _stall_dedupe_key(
            case_id=int(c.id),
            case_status=c.status or "",
            stall_type=stall_type,
            threshold_hours=threshold_hours,
            last_meaningful_event_id=last_meaningful_event_id,
        )

        # HARD DEDUPE: already logged stall_detected for same stall_key
        if ops.case_event_exists_payload_key(
            case_id=int(c.id),
            event_type="stall_detected",
            key="stall_key",
            value=stall_key,
        ):
            continue

        # fallback spam control
        if not _should_renotify(ops, int(c.id), stall_type):
            continue

        stalled += 1

        ops.create_case_event(
            case_id=int(c.id),
            email_id=None,
            event_type="stall_detected",
            actor="ai",
            payload={
                "case_status": c.status,
                "stall_type": stall_type,
                "stall_key": stall_key,
                "threshold_hours": threshold_hours,
                "hours_idle": round(hours_idle, 2),
                "last_event_type": getattr(last_evt, "event_type", None) if last_evt else None,
                "last_event_id": last_meaningful_event_id or None,
                "last_event_at": last_dt.isoformat() if last_dt else None,
            },
        )
        stalls_logged += 1

        if WATCHER_CREATE_DRAFTS:
            try:
                did = _create_graph_reply_followup_draft(ops, int(c.id), stall_type, stall_key)
                if did:
                    drafts_created += 1
            except Exception as e:
                audit_print(
                    "case_watcher.draft_error",
                    {"case_id": int(c.id), "error": str(e), "stall_type": stall_type},
                )

    out = {
        "scanned": scanned,
        "stalled": stalled,
        "stalls_logged": stalls_logged,
        "drafts_created": drafts_created,
    }
    audit_print("case_watcher.run_once", out)
    return out


def run_forever() -> None:
    interval = int(os.getenv("WATCHER_INTERVAL_SECONDS", "1800"))
    while True:
        try:
            run_once()
        except Exception as e:
            audit_print("case_watcher.error", {"error": str(e)})
        time.sleep(interval)


if __name__ == "__main__":
    run_forever()
