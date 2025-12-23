# from __future__ import annotations
# from typing import Optional, Dict, Any, List

# import hashlib
# from sqlalchemy import select
# from sqlalchemy import or_

# from app.db import SessionLocal
# from app.models import Email, SyncState, Case, Draft, EmailAttachment, CaseEvent

# import json
# from datetime import datetime, time, timedelta, timezone


# def _message_id_hash(message_id: str) -> bytes:
#     """
#     Returns 16-byte MD5 hash for message_id
#     Matches MySQL BINARY(16)
#     """
#     return hashlib.md5(message_id.encode("utf-8")).digest()


# def _clean_subject_for_case(subject: str | None) -> str:
#     s = (subject or "").strip()
#     if not s:
#         return "No subject"
#     return s[:500]


# class MysqlOps:
#     def list_all_drafts(self, limit: int = 20, tone: Optional[str] = None, kind: Optional[str] = None, requires_approval: Optional[int] = None):
#         """
#         Fetch all drafts with optional filters for tone, kind, and approval status.
#         """
#         with SessionLocal() as db:
#             query = select(Draft).order_by(Draft.id.desc()).limit(limit)

#             if tone:
#                 query = query.where(Draft.tone == tone)
#             if kind:
#                 query = query.where(Draft.kind == kind)
#             if requires_approval is not None:
#                 query = query.where(Draft.requires_approval == requires_approval)

#             return list(db.scalars(query))
#     # ---------- Sync State ----------
#     def get_sync_state(self, mailbox: str) -> Optional[SyncState]:
#         with SessionLocal() as db:
#             return db.scalar(select(SyncState).where(SyncState.mailbox == mailbox))

#     def upsert_sync_state(
#         self,
#         mailbox: str,
#         delta_link: Optional[str],
#         last_sync_iso: Optional[str],
#     ) -> None:
#         with SessionLocal() as db:
#             row = db.scalar(select(SyncState).where(SyncState.mailbox == mailbox))
#             if row:
#                 row.delta_link = delta_link
#                 row.last_sync_iso = last_sync_iso
#             else:
#                 row = SyncState(
#                     mailbox=mailbox,
#                     delta_link=delta_link,
#                     last_sync_iso=last_sync_iso,
#                 )
#                 db.add(row)
#             db.commit()

#     # ---------- Emails ----------
#     def upsert_email(self, e: Dict[str, Any]) -> int:
#         """
#         Insert if new; update if message_id_hash already exists.
#         Returns Email.id
#         """
#         message_id = e["message_id"]
#         if not message_id:
#             raise ValueError("Missing message_id")
#         msg_hash = _message_id_hash(message_id)

#         # ALWAYS coerce raw payload to string
#         raw = e.get("raw")
#         raw_str = json.dumps(raw, ensure_ascii=False, default=str) if isinstance(raw, (dict, list)) else raw

#         with SessionLocal() as db:
#             row = db.scalar(
#                 select(Email)
#                 .where(Email.mailbox == e.get("mailbox"))
#                 .where(Email.message_id_hash == msg_hash)
#             )

#             if row:
#                 row.mailbox = e.get("mailbox")
#                 row.case_id = e.get("case_id")
#                 row.message_id = message_id
#                 row.message_id_hash = msg_hash
#                 row.internet_message_id = e.get("internet_message_id")
#                 row.subject = e.get("subject")
#                 row.sender = e.get("sender")
#                 row.sender_name = e.get("sender_name")
#                 row.to_list = ",".join(e.get("to") or [])
#                 row.cc_list = ",".join(e.get("cc") or [])
#                 row.received_datetime = e.get("received_datetime")
#                 row.body_preview = e.get("body_preview")
#                 row.body_html = e.get("body_html")
#                 row.conversation_id = e.get("conversation_id")
#                 row.raw_json = raw_str
#                 db.commit()
#                 return row.id

#             row = Email(
#                 mailbox=e.get("mailbox"),
#                 case_id=e.get("case_id"),
#                 message_id=message_id,
#                 message_id_hash=msg_hash,
#                 internet_message_id=e.get("internet_message_id"),
#                 subject=e.get("subject"),
#                 sender=e.get("sender"),
#                 sender_name=e.get("sender_name"),
#                 to_list=",".join(e.get("to") or []),
#                 cc_list=",".join(e.get("cc") or []),
#                 received_datetime=e.get("received_datetime"),
#                 body_preview=e.get("body_preview"),
#                 body_html=e.get("body_html"),
#                 conversation_id=e.get("conversation_id"),
#                 raw_json=raw_str,
#             )
#             db.add(row)
#             db.commit()
#             db.refresh(row)
#             return row.id

#     def upsert_email_attachment(self, email_id: int, a: Dict[str, Any], local_path: str | None) -> None:
#         with SessionLocal() as db:
#             row = db.scalar(
#                 select(EmailAttachment)
#                 .where(EmailAttachment.email_id == email_id)
#                 .where(EmailAttachment.attachment_id == a.get("id"))
#             )

#             if row:
#                 # Update details (especially local_path) if we learned more
#                 row.name = row.name or a.get("name")
#                 row.content_type = row.content_type or (a.get("contentType") or a.get("content_type"))
#                 row.size = row.size or a.get("size")
#                 row.is_inline = 1 if a.get("isInline") else (row.is_inline or 0)
#                 row.content_id = row.content_id or a.get("contentId")

#                 if local_path and not row.local_path:
#                     row.local_path = local_path

#                 db.commit()
#                 return

#             row = EmailAttachment(
#                 email_id=email_id,
#                 attachment_id=a.get("id"),
#                 name=a.get("name"),
#                 content_type=a.get("contentType") or a.get("content_type"),
#                 size=a.get("size"),
#                 is_inline=1 if a.get("isInline") else 0,
#                 content_id=a.get("contentId"),
#                 local_path=local_path,
#             )
#             db.add(row)
#             db.commit()

#     def get_email_by_id(self, email_id: int) -> Optional[Email]:
#         with SessionLocal() as db:
#             return db.get(Email, email_id)

#     def list_emails(self, limit: int = 50) -> List[Email]:
#         with SessionLocal() as db:
#             return list(
#                 db.scalars(
#                     select(Email)
#                     .filter(
#                         or_(
#                         # Email.subject != None,
#                         # Email.subject != '',
#                         # Email.sender != None,
#                         Email.sender != '',
#                         # Email.sender_name != None,
#                         Email.sender_name != '',
#                         Email.received_datetime != None
#                     )
#                     )
#                     .order_by(Email.id.desc())
#                     .limit(limit)
#                 )
#             )

#     def get_latest_draft_for_case_kind(self, case_id: int, kind: str) -> Optional[Draft]:
#         with SessionLocal() as db:
#             return db.scalar(
#                 select(Draft)
#                 .join(Email, Email.id == Draft.email_id)
#                 .where(Email.case_id == case_id)
#                 .where(Draft.kind == kind)
#                 .order_by(Draft.id.desc())
#                 .limit(1)
#             )

#     # ---------- Drafts ----------
#     def create_draft(
#         self,
#         email_id: int,
#         draft: str,
#         model: str,
#         tone: Optional[str] = None,
#         mailbox: Optional[str] = None,
#         graph_draft_message_id: Optional[str] = None,
#         graph_draft_web_link: Optional[str] = None,
#         # NEW
#         kind: Optional[str] = None,
#         requires_approval: int = 1,
#         approved_by: Optional[str] = None,
#         approved_at: Optional[datetime] = None,
#     ) -> int:
#         with SessionLocal() as db:
#             row = Draft(
#                 email_id=email_id,
#                 draft=draft,
#                 model=model,
#                 tone=tone,
#                 mailbox=mailbox,
#                 graph_draft_message_id=graph_draft_message_id,
#                 graph_draft_web_link=graph_draft_web_link,
#                 # NEW
#                 kind=kind,
#                 requires_approval=int(requires_approval),
#                 approved_by=approved_by,
#                 approved_at=approved_at,
#             )
#             db.add(row)
#             db.commit()
#             db.refresh(row)
#             return row.id

#     def update_draft_text(self, draft_id: int, draft: str) -> None:
#         """
#         Update draft body text in DB (used by API PUT /drafts/{draft_id}).
#         Added carefully without touching other behavior.
#         """
#         with SessionLocal() as db:
#             row = db.get(Draft, draft_id)
#             if not row:
#                 raise ValueError("Draft not found")
#             row.draft = draft
#             db.commit()

#     def update_draft(self, draft_id: int, fields: Dict[str, Any]) -> None:
#         """
#         Generic draft update helper (fallback if callers want to update multiple columns).
#         Added carefully without touching other behavior.
#         """
#         with SessionLocal() as db:
#             row = db.get(Draft, draft_id)
#             if not row:
#                 raise ValueError("Draft not found")
#             for k, v in fields.items():
#                 setattr(row, k, v)
#             db.commit()

#     # ---------- Cases ----------
#     def list_cases(self) -> List[Case]:
#         with SessionLocal() as db:
#             return list(
#                 db.scalars(
#                     select(Case).order_by(Case.id.desc())
#                 )
#             )

#     def create_case(
#             self,
#             external_id: Optional[str],
#             title: str,
#             status: str,
#             metadata: Optional[Dict[str, Any]],
#     ) -> int:
#         with SessionLocal() as db:
#             row = Case(
#                 external_id=external_id,
#                 title=title,
#                 status=status,
#                 metadata_json=metadata or {},
#             )
#             db.add(row)
#             db.commit()
#             db.refresh(row)
#             return row.id

#     def update_case(self, case_id: int, fields: Dict[str, Any]) -> None:
#         with SessionLocal() as db:
#             row = db.get(Case, case_id)
#             if not row:
#                 raise ValueError("Case not found")
#             for k, v in fields.items():
#                 setattr(row, k, v)
#             db.commit()

#     # MISSING FUNCTION (required by poller and API routes)
#     def get_case_by_id(self, case_id: int) -> Optional[Case]:
#         with SessionLocal() as db:
#             return db.get(Case, case_id)

#     def get_latest_email_for_case(self, case_id: int) -> Optional[Email]:
#         with SessionLocal() as db:
#             return db.scalar(
#                 select(Email)
#                 .where(Email.case_id == case_id)
#                 .order_by(Email.id.desc())
#                 .limit(1)
#             )

#     # ---------------------------
#     # CaseEvent payload helpers
#     # ---------------------------
#     def _payload_as_dict(self, p: Any) -> dict:
#         """
#         Normalize payload_json to a dict safely.
#         NOTE: This function existed twice in your pasted file; keep only one.
#         """
#         if p is None:
#             return {}
#         if isinstance(p, dict):
#             return p
#         if isinstance(p, str):
#             try:
#                 return json.loads(p)
#             except Exception:
#                 return {}
#         return {}

#     def case_event_exists_payload_key(
#         self,
#         case_id: int,
#         event_type: str,
#         key: str,
#         value: str,
#         scan_limit: int = 50,
#     ) -> bool:
#         """
#         Idempotency guard without schema changes.
#         Fetch latest N events of a type and check payload[key] == value in Python.
#         NOTE: This function existed twice in your pasted file; keep only one.
#         """
#         with SessionLocal() as db:
#             rows = list(
#                 db.scalars(
#                     select(CaseEvent)
#                     .where(CaseEvent.case_id == case_id)
#                     .where(CaseEvent.event_type == event_type)
#                     .order_by(CaseEvent.created_at.desc())
#                     .limit(scan_limit)
#                 )
#             )

#         for r in rows:
#             p = self._payload_as_dict(getattr(r, "payload_json", None))
#             if (p or {}).get(key) == value:
#                 return True
#         return False

#     # ---------- Draft reads ----------
#     def get_draft_by_id(self, draft_id: int) -> Optional[Draft]:
#         with SessionLocal() as db:
#             return db.get(Draft, draft_id)

#     def list_drafts_for_email(self, email_id: int, limit: int = 20) -> List[Draft]:
#         with SessionLocal() as db:
#             return list(
#                 db.scalars(
#                     select(Draft)
#                     .where(Draft.email_id == email_id)
#                     .order_by(Draft.id.desc())
#                     .limit(limit)
#                 )
#             )

#     def get_latest_draft_for_email(self, email_id: int) -> Optional[Draft]:
#         with SessionLocal() as db:
#             return db.scalar(
#                 select(Draft)
#                 .where(Draft.email_id == email_id)
#                 .order_by(Draft.id.desc())
#                 .limit(1)
#             )

#     def mark_draft_sent(self, draft_id: int, mailbox: str, sent_message_id: Optional[str] = None) -> None:
#         with SessionLocal() as db:
#             row = db.get(Draft, draft_id)
#             if not row:
#                 raise ValueError("Draft not found")
#             row.status = "sent"
#             row.mailbox = mailbox
#             row.sent_message_id = sent_message_id
#             row.sent_at = datetime.now(timezone.utc)
#             db.commit()

#     # ---------- Case/email relations ----------
#     def list_emails_for_case(self, case_id: int, limit: int = 200) -> List[Email]:
#         with SessionLocal() as db:
#             return list(
#                 db.scalars(
#                     select(Email)
#                     .where(Email.case_id == case_id)
#                     .order_by(Email.received_datetime.asc())
#                     .limit(limit)
#                 )
#             )

#     def get_case_id_by_conversation(self, mailbox: str, conversation_id: str) -> Optional[int]:
#         if not conversation_id:
#             return None
#         with SessionLocal() as db:
#             row = db.scalar(
#                 select(Email.case_id)
#                 .where(Email.mailbox == mailbox)
#                 .where(Email.conversation_id == conversation_id)
#                 .where(Email.case_id.isnot(None))
#                 .order_by(Email.id.asc())
#                 .limit(1)
#             )
#             return int(row) if row else None

#     def get_or_create_case_for_email(self, email: Dict[str, Any], mailbox: str, email_id: int) -> int:
#         conv_id = (email.get("conversation_id") or "").strip()

#         # 1) try existing case for this conversation in this mailbox
#         existing_case_id = self.get_case_id_by_conversation(mailbox, conv_id) if conv_id else None
#         if existing_case_id:
#             return existing_case_id

#         # 2) create new case
#         title = _clean_subject_for_case(email.get("subject"))
#         external_id = email.get("message_id")  # ok as a starter (or conversation_id if you prefer)

#         with SessionLocal() as db:
#             row = Case(
#                 external_id=external_id,
#                 title=title,
#                 status="new",
#                 metadata_json={
#                     "mailbox": mailbox,
#                     "conversation_id": conv_id,
#                     "seed_email_id": email_id,
#                 },
#             )
#             db.add(row)
#             db.commit()
#             db.refresh(row)
#             return row.id

#     def list_attachments_for_email(self, email_id: int) -> List[EmailAttachment]:
#         with SessionLocal() as db:
#             return list(
#                 db.scalars(
#                     select(EmailAttachment)
#                     .where(EmailAttachment.email_id == email_id)
#                     .order_by(EmailAttachment.id.asc())
#                 )
#             )

#     def set_email_case_id(self, email_id: int, case_id: int) -> None:
#         with SessionLocal() as db:
#             row = db.get(Email, email_id)
#             if not row:
#                 raise ValueError("Email not found")
#             row.case_id = case_id
#             db.commit()

#     def get_or_create_case_by_external_id(self, external_id: str, title: str, metadata: dict | None = None) -> int:
#         if not external_id:
#             raise ValueError("external_id is required")

#         with SessionLocal() as db:
#             row = db.scalar(select(Case).where(Case.external_id == external_id))
#             if row:
#                 # Keep title stable unless current one is empty
#                 if (not row.title) and title:
#                     row.title = _clean_subject_for_case(title)
#                     db.commit()
#                 return row.id

#             row = Case(
#                 external_id=external_id,
#                 title=_clean_subject_for_case(title),
#                 status="new",
#                 metadata_json=metadata or {},
#             )
#             db.add(row)
#             db.commit()
#             db.refresh(row)
#             return row.id

#     # ---------- Events ----------
#     def create_case_event(
#         self,
#         case_id: int,
#         event_type: str,
#         email_id: int | None = None,
#         actor: str = "ai",
#         payload: dict | None = None,
#     ) -> int:
#         from app.models import CaseEvent

#         with SessionLocal() as db:
#             row = CaseEvent(
#                 case_id=case_id,
#                 email_id=email_id,
#                 event_type=event_type,
#                 actor=actor,
#                 payload_json=payload or {},
#                 created_at=datetime.now(timezone.utc),  # FORCE IT
#             )
#             db.add(row)
#             db.commit()
#             db.refresh(row)
#             return row.id

#     def set_email_received_at(self, email_id: int, received_at) -> None:
#         with SessionLocal() as db:
#             row = db.get(Email, email_id)
#             if not row:
#                 return
#             row.received_at = received_at
#             db.commit()

#     def case_event_exists(self, case_id: int, email_id: int, event_type: str) -> bool:
#         from app.models import CaseEvent
#         with SessionLocal() as db:
#             row = db.scalar(
#                 select(CaseEvent.id)
#                 .where(CaseEvent.case_id == case_id)
#                 .where(CaseEvent.email_id == email_id)
#                 .where(CaseEvent.event_type == event_type)
#                 .limit(1)
#             )
#             return bool(row)

#     def case_event_exists_any(self, case_id: int, email_id: int | None, event_type: str) -> bool:
#         """
#         Handles email_id None properly (MySQL UNIQUE allows multiple NULLs, so we must guard in code).
#         NOTE: This function existed twice in your pasted file; keep only one.
#         """
#         with SessionLocal() as db:
#             q = select(CaseEvent.id).where(
#                 CaseEvent.case_id == case_id,
#                 CaseEvent.event_type == event_type,
#             )

#             if email_id is None:
#                 q = q.where(CaseEvent.email_id.is_(None))
#             else:
#                 q = q.where(CaseEvent.email_id == email_id)

#             row = db.scalar(q.limit(1))
#             return bool(row)

#     def get_latest_case_event(self, case_id: int, event_type: str) -> Optional[CaseEvent]:
#         with SessionLocal() as db:
#             return db.scalar(
#                 select(CaseEvent)
#                 .where(CaseEvent.case_id == case_id)
#                 .where(CaseEvent.event_type == event_type)
#                 .order_by(CaseEvent.created_at.desc())
#                 .limit(1)
#             )

#     def get_latest_stall_event(self, case_id: int, stall_type: str) -> Optional[CaseEvent]:
#         with SessionLocal() as db:
#             rows = list(
#                 db.scalars(
#                     select(CaseEvent)
#                     .where(CaseEvent.case_id == case_id)
#                     .where(CaseEvent.event_type == "stall_detected")
#                     .order_by(CaseEvent.created_at.desc())
#                     .limit(25)
#                 )
#             )

#         for r in rows:
#             p = self._payload_as_dict(getattr(r, "payload_json", None))
#             if (p or {}).get("stall_type") == stall_type:
#                 return r
#         return None

#     # ---------- Watcher helpers ----------
#     def list_active_cases(self, limit: int = 500) -> List[Case]:
#         with SessionLocal() as db:
#             return list(
#                 db.scalars(
#                     select(Case)
#                     .where(Case.status != "closed")
#                     .order_by(Case.updated_at.desc())
#                     .limit(limit)
#                 )
#             )

#     def get_latest_meaningful_event(self, case_id: int) -> Optional[CaseEvent]:
#         ignore = {"llm_processed", "stall_detected", "followup_draft_created"}
#         with SessionLocal() as db:
#             return db.scalar(
#                 select(CaseEvent)
#                 .where(CaseEvent.case_id == case_id)
#                 .where(CaseEvent.event_type.notin_(ignore))
#                 .order_by(CaseEvent.created_at.desc())
#                 .limit(1)
#             )

#     # ---------- Case metadata ----------
#     def merge_case_metadata(self, case_id: int, patch: dict) -> None:
#         """
#         Merge patch into metadata_json (shallow merge).
#         """
#         with SessionLocal() as db:
#             row = db.get(Case, case_id)
#             if not row:
#                 raise ValueError("Case not found")

#             base = row.metadata_json or {}

#             if isinstance(base, str):
#                 try:
#                     base = json.loads(base)
#                 except Exception:
#                     base = {}

#             if not isinstance(base, dict):
#                 base = {}

#             if isinstance(patch, str):
#                 try:
#                     patch = json.loads(patch)
#                 except Exception:
#                     patch = {}

#             if not isinstance(patch, dict):
#                 patch = {}

#             base.update(patch)
#             row.metadata_json = base
#             db.commit()

#     # ---------- Attachments ----------
#     def set_attachment_openai_file_id(self, attachment_row_id: int, openai_file_id: str) -> None:
#         with SessionLocal() as db:
#             row = db.get(EmailAttachment, attachment_row_id)
#             if not row:
#                 return
#             row.openai_file_id = openai_file_id
#             db.commit()

#     def get_attachments_for_email_full(self, email_id: int) -> List[EmailAttachment]:
#         with SessionLocal() as db:
#             return list(
#                 db.scalars(
#                     select(EmailAttachment)
#                     .where(EmailAttachment.email_id == email_id)
#                     .order_by(EmailAttachment.id.asc())
#                 )
#             )
#     def check_stalled_cases(self, stall_timeout_hours: float) -> List[Dict[str, Any]]:
#         """
#         Check for cases that have been idle for longer than the given stall timeout hours.
#         Returns a list of stalled cases and the notifications to be created.
#         """
#         current_time = datetime.now(timezone.utc)
        
#         # Ensure the session is used correctly
#         with SessionLocal() as db:
#             # Query for cases that have been idle beyond the stall timeout
#             cases = db.query(Case).filter(Case.updated_at < current_time - timedelta(hours=stall_timeout_hours)).all()

#         stalled_cases = []
#         for case in cases:
#             # Calculate idle hours
#             idle_hours = (current_time - case.updated_at).total_seconds() / 3600  # Convert seconds to hours
            
#             if idle_hours >= stall_timeout_hours:
#                 stalled_cases.append({
#                     "case_id": case.id,
#                     "message": f"Case {case.id} has been idle for more than {stall_timeout_hours} hours.",
#                     "status": "new",  # Flag as new notification
#                     "timestamp": time.time()  # Track when the notification was created
#                 })
        
#         return stalled_cases



















from __future__ import annotations
from typing import Optional, Dict, Any, List

import hashlib
from sqlalchemy import select
from sqlalchemy import or_

from app.db import SessionLocal
from app.models import Email, SyncState, Case, Draft, EmailAttachment, CaseEvent

import json
from datetime import datetime, time, timedelta, timezone


def _message_id_hash(message_id: str) -> bytes:
    """
    Returns 16-byte MD5 hash for message_id
    Matches MySQL BINARY(16)
    """
    return hashlib.md5(message_id.encode("utf-8")).digest()


def _clean_subject_for_case(subject: str | None) -> str:
    s = (subject or "").strip()
    if not s:
        return "No subject"
    return s[:500]


class MysqlOps:
    def list_all_drafts(self, limit: int = 20, tone: Optional[str] = None, kind: Optional[str] = None, requires_approval: Optional[int] = None):
        """
        Fetch all drafts with optional filters for tone, kind, and approval status.
        """
        with SessionLocal() as db:
            query = select(Draft).order_by(Draft.id.desc()).limit(limit)

            if tone:
                query = query.where(Draft.tone == tone)
            if kind:
                query = query.where(Draft.kind == kind)
            if requires_approval is not None:
                query = query.where(Draft.requires_approval == requires_approval)

            return list(db.scalars(query))
    # ---------- Sync State ----------
    def get_sync_state(self, mailbox: str) -> Optional[SyncState]:
        with SessionLocal() as db:
            return db.scalar(select(SyncState).where(SyncState.mailbox == mailbox))

    def upsert_sync_state(
        self,
        mailbox: str,
        delta_link: Optional[str],
        last_sync_iso: Optional[str],
    ) -> None:
        with SessionLocal() as db:
            row = db.scalar(select(SyncState).where(SyncState.mailbox == mailbox))
            if row:
                row.delta_link = delta_link
                row.last_sync_iso = last_sync_iso
            else:
                row = SyncState(
                    mailbox=mailbox,
                    delta_link=delta_link,
                    last_sync_iso=last_sync_iso,
                )
                db.add(row)
            db.commit()

    # ---------- Emails ----------
    def upsert_email(self, e: Dict[str, Any]) -> int:
        """
        Insert if new; update if message_id_hash already exists.
        Returns Email.id
        """
        message_id = e["message_id"]
        if not message_id:
            raise ValueError("Missing message_id")
        msg_hash = _message_id_hash(message_id)

        # ALWAYS coerce raw payload to string
        raw = e.get("raw")
        raw_str = json.dumps(raw, ensure_ascii=False, default=str) if isinstance(raw, (dict, list)) else raw

        with SessionLocal() as db:
            row = db.scalar(
                select(Email)
                .where(Email.mailbox == e.get("mailbox"))
                .where(Email.message_id_hash == msg_hash)
            )

            if row:
                row.mailbox = e.get("mailbox")
                row.case_id = e.get("case_id")
                row.message_id = message_id
                row.message_id_hash = msg_hash
                row.internet_message_id = e.get("internet_message_id")
                row.subject = e.get("subject")
                row.sender = e.get("sender")
                row.sender_name = e.get("sender_name")
                row.to_list = ",".join(e.get("to") or [])
                row.cc_list = ",".join(e.get("cc") or [])
                row.received_datetime = e.get("received_datetime")
                row.body_preview = e.get("body_preview")
                row.body_html = e.get("body_html")
                row.conversation_id = e.get("conversation_id")
                row.raw_json = raw_str
                db.commit()
                return row.id

            row = Email(
                mailbox=e.get("mailbox"),
                case_id=e.get("case_id"),
                message_id=message_id,
                message_id_hash=msg_hash,
                internet_message_id=e.get("internet_message_id"),
                subject=e.get("subject"),
                sender=e.get("sender"),
                sender_name=e.get("sender_name"),
                to_list=",".join(e.get("to") or []),
                cc_list=",".join(e.get("cc") or []),
                received_datetime=e.get("received_datetime"),
                body_preview=e.get("body_preview"),
                body_html=e.get("body_html"),
                conversation_id=e.get("conversation_id"),
                raw_json=raw_str,
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return row.id

    def upsert_email_attachment(self, email_id: int, a: Dict[str, Any], local_path: str | None) -> None:
        with SessionLocal() as db:
            row = db.scalar(
                select(EmailAttachment)
                .where(EmailAttachment.email_id == email_id)
                .where(EmailAttachment.attachment_id == a.get("id"))
            )

            if row:
                # Update details (especially local_path) if we learned more
                row.name = row.name or a.get("name")
                row.content_type = row.content_type or (a.get("contentType") or a.get("content_type"))
                row.size = row.size or a.get("size")
                row.is_inline = 1 if a.get("isInline") else (row.is_inline or 0)
                row.content_id = row.content_id or a.get("contentId")

                if local_path and not row.local_path:
                    row.local_path = local_path

                db.commit()
                return

            row = EmailAttachment(
                email_id=email_id,
                attachment_id=a.get("id"),
                name=a.get("name"),
                content_type=a.get("contentType") or a.get("content_type"),
                size=a.get("size"),
                is_inline=1 if a.get("isInline") else 0,
                content_id=a.get("contentId"),
                local_path=local_path,
            )
            db.add(row)
            db.commit()

    def get_email_by_id(self, email_id: int) -> Optional[Email]:
        with SessionLocal() as db:
            return db.get(Email, email_id)

    def list_emails(self, limit: int = 50) -> List[Email]:
        with SessionLocal() as db:
            return list(
                db.scalars(
                    select(Email)
                    .filter(
                        or_(
                        # Email.subject != None,
                        # Email.subject != '',
                        # Email.sender != None,
                        Email.sender != '',
                        # Email.sender_name != None,
                        Email.sender_name != '',
                        Email.received_datetime != None
                    )
                    )
                    .order_by(Email.id.desc())
                    .limit(limit)
                )
            )

    def get_latest_draft_for_case_kind(self, case_id: int, kind: str) -> Optional[Draft]:
        with SessionLocal() as db:
            return db.scalar(
                select(Draft)
                .join(Email, Email.id == Draft.email_id)
                .where(Email.case_id == case_id)
                .where(Draft.kind == kind)
                .order_by(Draft.id.desc())
                .limit(1)
            )

    # ---------- Drafts ----------
    def create_draft(
        self,
        email_id: int,
        draft: str,
        model: str,
        tone: Optional[str] = None,
        mailbox: Optional[str] = None,
        graph_draft_message_id: Optional[str] = None,
        graph_draft_web_link: Optional[str] = None,
        # NEW
        kind: Optional[str] = None,
        requires_approval: int = 1,
        approved_by: Optional[str] = None,
        approved_at: Optional[datetime] = None,
    ) -> int:
        with SessionLocal() as db:
            row = Draft(
                email_id=email_id,
                draft=draft,
                model=model,
                tone=tone,
                mailbox=mailbox,
                graph_draft_message_id=graph_draft_message_id,
                graph_draft_web_link=graph_draft_web_link,
                # NEW
                kind=kind,
                requires_approval=int(requires_approval),
                approved_by=approved_by,
                approved_at=approved_at,
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return row.id

    def update_draft_text(self, draft_id: int, draft: str) -> None:
        """
        Update draft body text in DB (used by API PUT /drafts/{draft_id}).
        Added carefully without touching other behavior.
        """
        with SessionLocal() as db:
            row = db.get(Draft, draft_id)
            if not row:
                raise ValueError("Draft not found")
            row.draft = draft
            db.commit()

    def update_draft(self, draft_id: int, fields: Dict[str, Any]) -> None:
        """
        Generic draft update helper (fallback if callers want to update multiple columns).
        Added carefully without touching other behavior.
        """
        with SessionLocal() as db:
            row = db.get(Draft, draft_id)
            if not row:
                raise ValueError("Draft not found")
            for k, v in fields.items():
                setattr(row, k, v)
            db.commit()

    # ---------- Cases ----------
    def list_cases(self) -> List[Case]:
        with SessionLocal() as db:
            return list(
                db.scalars(
                    select(Case).order_by(Case.id.desc())
                )
            )

    def create_case(
            self,
            external_id: Optional[str],
            title: str,
            status: str,
            metadata: Optional[Dict[str, Any]],
    ) -> int:
        with SessionLocal() as db:
            row = Case(
                external_id=external_id,
                title=title,
                status=status,
                metadata_json=metadata or {},
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return row.id

    def update_case(self, case_id: int, fields: Dict[str, Any]) -> None:
        with SessionLocal() as db:
            row = db.get(Case, case_id)
            if not row:
                raise ValueError("Case not found")
            for k, v in fields.items():
                setattr(row, k, v)
            db.commit()

    # MISSING FUNCTION (required by poller and API routes)
    def get_case_by_id(self, case_id: int) -> Optional[Case]:
        with SessionLocal() as db:
            return db.get(Case, case_id)

    def get_latest_email_for_case(self, case_id: int) -> Optional[Email]:
        with SessionLocal() as db:
            return db.scalar(
                select(Email)
                .where(Email.case_id == case_id)
                .order_by(Email.id.desc())
                .limit(1)
            )

    # ---------------------------
    # CaseEvent payload helpers
    # ---------------------------
    def _payload_as_dict(self, p: Any) -> dict:
        """
        Normalize payload_json to a dict safely.
        NOTE: This function existed twice in your pasted file; keep only one.
        """
        if p is None:
            return {}
        if isinstance(p, dict):
            return p
        if isinstance(p, str):
            try:
                return json.loads(p)
            except Exception:
                return {}
        return {}

    def case_event_exists_payload_key(
        self,
        case_id: int,
        event_type: str,
        key: str,
        value: str,
        scan_limit: int = 50,
    ) -> bool:
        """
        Idempotency guard without schema changes.
        Fetch latest N events of a type and check payload[key] == value in Python.
        NOTE: This function existed twice in your pasted file; keep only one.
        """
        with SessionLocal() as db:
            rows = list(
                db.scalars(
                    select(CaseEvent)
                    .where(CaseEvent.case_id == case_id)
                    .where(CaseEvent.event_type == event_type)
                    .order_by(CaseEvent.created_at.desc())
                    .limit(scan_limit)
                )
            )

        for r in rows:
            p = self._payload_as_dict(getattr(r, "payload_json", None))
            if (p or {}).get(key) == value:
                return True
        return False

    # ---------- Draft reads ----------
    def get_draft_by_id(self, draft_id: int) -> Optional[Draft]:
        with SessionLocal() as db:
            return db.get(Draft, draft_id)

    def list_drafts_for_email(self, email_id: int, limit: int = 20) -> List[Draft]:
        with SessionLocal() as db:
            return list(
                db.scalars(
                    select(Draft)
                    .where(Draft.email_id == email_id)
                    .order_by(Draft.id.desc())
                    .limit(limit)
                )
            )

    def get_latest_draft_for_email(self, email_id: int) -> Optional[Draft]:
        with SessionLocal() as db:
            return db.scalar(
                select(Draft)
                .where(Draft.email_id == email_id)
                .order_by(Draft.id.desc())
                .limit(1)
            )

    def mark_draft_sent(self, draft_id: int, mailbox: str, sent_message_id: Optional[str] = None) -> None:
        with SessionLocal() as db:
            row = db.get(Draft, draft_id)
            if not row:
                raise ValueError("Draft not found")
            row.status = "sent"
            row.mailbox = mailbox
            row.sent_message_id = sent_message_id
            row.sent_at = datetime.now(timezone.utc)
            db.commit()

    # ---------- Case/email relations ----------
    def list_emails_for_case(self, case_id: int, limit: int = 200) -> List[Email]:
        with SessionLocal() as db:
            return list(
                db.scalars(
                    select(Email)
                    .where(Email.case_id == case_id)
                    .order_by(Email.received_datetime.asc())
                    .limit(limit)
                )
            )

    def get_case_id_by_conversation(self, mailbox: str, conversation_id: str) -> Optional[int]:
        if not conversation_id:
            return None
        with SessionLocal() as db:
            row = db.scalar(
                select(Email.case_id)
                .where(Email.mailbox == mailbox)
                .where(Email.conversation_id == conversation_id)
                .where(Email.case_id.isnot(None))
                .order_by(Email.id.asc())
                .limit(1)
            )
            return int(row) if row else None

    def get_or_create_case_for_email(self, email: Dict[str, Any], mailbox: str, email_id: int) -> int:
        conv_id = (email.get("conversation_id") or "").strip()

        # 1) try existing case for this conversation in this mailbox
        existing_case_id = self.get_case_id_by_conversation(mailbox, conv_id) if conv_id else None
        if existing_case_id:
            return existing_case_id

        # 2) create new case
        title = _clean_subject_for_case(email.get("subject"))
        external_id = email.get("message_id")  # ok as a starter (or conversation_id if you prefer)

        with SessionLocal() as db:
            row = Case(
                external_id=external_id,
                title=title,
                status="new",
                metadata_json={
                    "mailbox": mailbox,
                    "conversation_id": conv_id,
                    "seed_email_id": email_id,
                },
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return row.id

    def list_attachments_for_email(self, email_id: int) -> List[EmailAttachment]:
        with SessionLocal() as db:
            return list(
                db.scalars(
                    select(EmailAttachment)
                    .where(EmailAttachment.email_id == email_id)
                    .order_by(EmailAttachment.id.asc())
                )
            )

    def set_email_case_id(self, email_id: int, case_id: int) -> None:
        with SessionLocal() as db:
            row = db.get(Email, email_id)
            if not row:
                raise ValueError("Email not found")
            row.case_id = case_id
            db.commit()

    def get_or_create_case_by_external_id(self, external_id: str, title: str, metadata: dict | None = None) -> int:
        if not external_id:
            raise ValueError("external_id is required")

        with SessionLocal() as db:
            row = db.scalar(select(Case).where(Case.external_id == external_id))
            if row:
                # Keep title stable unless current one is empty
                if (not row.title) and title:
                    row.title = _clean_subject_for_case(title)
                    db.commit()
                return row.id

            row = Case(
                external_id=external_id,
                title=_clean_subject_for_case(title),
                status="new",
                metadata_json=metadata or {},
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return row.id

    # ---------- Events ----------
    def create_case_event(
        self,
        case_id: int,
        event_type: str,
        email_id: int | None = None,
        actor: str = "ai",
        payload: dict | None = None,
    ) -> int:
        from app.models import CaseEvent

        with SessionLocal() as db:
            row = CaseEvent(
                case_id=case_id,
                email_id=email_id,
                event_type=event_type,
                actor=actor,
                payload_json=payload or {},
                created_at=datetime.now(timezone.utc),  # FORCE IT
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return row.id

    def set_email_received_at(self, email_id: int, received_at) -> None:
        with SessionLocal() as db:
            row = db.get(Email, email_id)
            if not row:
                return
            row.received_at = received_at
            db.commit()

    def case_event_exists(self, case_id: int, email_id: int, event_type: str) -> bool:
        from app.models import CaseEvent
        with SessionLocal() as db:
            row = db.scalar(
                select(CaseEvent.id)
                .where(CaseEvent.case_id == case_id)
                .where(CaseEvent.email_id == email_id)
                .where(CaseEvent.event_type == event_type)
                .limit(1)
            )
            return bool(row)

    def case_event_exists_any(self, case_id: int, email_id: int | None, event_type: str) -> bool:
        """
        Handles email_id None properly (MySQL UNIQUE allows multiple NULLs, so we must guard in code).
        NOTE: This function existed twice in your pasted file; keep only one.
        """
        with SessionLocal() as db:
            q = select(CaseEvent.id).where(
                CaseEvent.case_id == case_id,
                CaseEvent.event_type == event_type,
            )

            if email_id is None:
                q = q.where(CaseEvent.email_id.is_(None))
            else:
                q = q.where(CaseEvent.email_id == email_id)

            row = db.scalar(q.limit(1))
            return bool(row)

    def get_latest_case_event(self, case_id: int, event_type: str) -> Optional[CaseEvent]:
        with SessionLocal() as db:
            return db.scalar(
                select(CaseEvent)
                .where(CaseEvent.case_id == case_id)
                .where(CaseEvent.event_type == event_type)
                .order_by(CaseEvent.created_at.desc())
                .limit(1)
            )

    def get_latest_stall_event(self, case_id: int, stall_type: str) -> Optional[CaseEvent]:
        with SessionLocal() as db:
            rows = list(
                db.scalars(
                    select(CaseEvent)
                    .where(CaseEvent.case_id == case_id)
                    .where(CaseEvent.event_type == "stall_detected")
                    .order_by(CaseEvent.created_at.desc())
                    .limit(25)
                )
            )

        for r in rows:
            p = self._payload_as_dict(getattr(r, "payload_json", None))
            if (p or {}).get("stall_type") == stall_type:
                return r
        return None

    # ---------- Watcher helpers ----------
    def list_active_cases(self, limit: int = 500) -> List[Case]:
        with SessionLocal() as db:
            return list(
                db.scalars(
                    select(Case)
                    .where(Case.status != "closed")
                    .order_by(Case.updated_at.desc())
                    .limit(limit)
                )
            )

    def get_latest_meaningful_event(self, case_id: int) -> Optional[CaseEvent]:
        ignore = {"llm_processed", "stall_detected", "followup_draft_created"}
        with SessionLocal() as db:
            return db.scalar(
                select(CaseEvent)
                .where(CaseEvent.case_id == case_id)
                .where(CaseEvent.event_type.notin_(ignore))
                .order_by(CaseEvent.created_at.desc())
                .limit(1)
            )

    # ---------- Case metadata ----------
    def merge_case_metadata(self, case_id: int, patch: dict) -> None:
        """
        Merge patch into metadata_json (shallow merge).
        """
        with SessionLocal() as db:
            row = db.get(Case, case_id)
            if not row:
                raise ValueError("Case not found")

            base = row.metadata_json or {}

            if isinstance(base, str):
                try:
                    base = json.loads(base)
                except Exception:
                    base = {}

            if not isinstance(base, dict):
                base = {}

            if isinstance(patch, str):
                try:
                    patch = json.loads(patch)
                except Exception:
                    patch = {}

            if not isinstance(patch, dict):
                patch = {}

            base.update(patch)
            row.metadata_json = base
            db.commit()

    # ---------- Attachments ----------
    def set_attachment_openai_file_id(self, attachment_row_id: int, openai_file_id: str) -> None:
        with SessionLocal() as db:
            row = db.get(EmailAttachment, attachment_row_id)
            if not row:
                return
            row.openai_file_id = openai_file_id
            db.commit()

    def get_attachments_for_email_full(self, email_id: int) -> List[EmailAttachment]:
        with SessionLocal() as db:
            return list(
                db.scalars(
                    select(EmailAttachment)
                    .where(EmailAttachment.email_id == email_id)
                    .order_by(EmailAttachment.id.asc())
                )
            )
    def check_stalled_cases(self, stall_timeout_hours: float) -> List[Dict[str, Any]]:
        """
        Check for cases that have been idle for longer than the given stall timeout hours.
        Returns a list of stalled cases and the notifications to be created.
        """
        current_time = datetime.now(timezone.utc)

        # Ensure the session is used correctly
        with SessionLocal() as db:
            # Query for cases that have been idle beyond the stall timeout
            cases = db.query(Case).filter(Case.updated_at < current_time - timedelta(hours=stall_timeout_hours)).all()

        stalled_cases = []
        for case in cases:
            # Calculate idle hours
            idle_hours = (current_time - case.updated_at).total_seconds() / 3600  # Convert seconds to hours

            if idle_hours >= stall_timeout_hours:
                stalled_cases.append({
                    "case_id": case.id,
                    "message": f"Case {case.id} has been idle for more than {stall_timeout_hours} hours.",
                    "status": "new",  # Flag as new notification
                    "timestamp": time.time()  # Track when the notification was created
                })

        return stalled_cases