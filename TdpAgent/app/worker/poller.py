# from __future__ import annotations

# import os
# import time
# import base64
# from datetime import datetime, timedelta, timezone

# from dotenv import load_dotenv
# load_dotenv()

# from app.core.audit import audit_print
# from app.graph.mail import (
#     fetch_messages_delta_for_mailbox,
#     fetch_messages_since_iso_for_mailbox,
#     prime_delta_cursor_for_mailbox,
#     to_email_item,
#     now_iso,
# )

# from app.graph.attachments import fetch_attachments
# from app.storage.attachments import save_file_attachment
# from app.mysql_ops import MysqlOps
# from app.ai.tasks import process_email_llm
# from app.core.intent_rules import can_apply_intent, status_for_intent
# from app.core.status_rules import normalize_status

# # NEW: auto-acceptance draft when staffing confirmed
# from app.ai.tasks import draft_case_acceptance
# from app.graph.reply import create_reply_draft, update_draft_message
# import html


# def _parse_graph_dt(dt_str: str | None):
#     if not dt_str:
#         return None
#     try:
#         if dt_str.endswith("Z"):
#             dt_str = dt_str.replace("Z", "+00:00")
#         return datetime.fromisoformat(dt_str)
#     except Exception:
#         return None


# def _is_image_attachment(a: dict) -> bool:
#     ct = (a.get("contentType") or "").lower()
#     name = (a.get("name") or "").lower()
#     return ct.startswith("image/") or name.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico"))


# def _should_skip_noise(a: dict, min_image_bytes: int) -> tuple[bool, str]:
#     if a.get("isInline") or a.get("contentId"):
#         return True, "inline"

#     if _is_image_attachment(a):
#         size = int(a.get("size") or 0)
#         if size and size < min_image_bytes:
#             return True, f"small_image<{min_image_bytes}"

#     return False, ""


# def _get_mailboxes() -> list[str]:
#     mailboxes = os.getenv("MAILBOXES", "").strip()
#     if mailboxes:
#         return [m.strip() for m in mailboxes.split(",") if m.strip()]
#     single = os.getenv("MS_USER_ID", "").strip()
#     if single:
#         return [single]
#     return []


# def _try_process_attachments(
#     ops: MysqlOps,
#     mailbox: str,
#     email_id: int,
#     graph_message_id: str,
# ) -> dict:
#     stats = {
#         "count": 0,
#         "saved_files": 0,
#         "saved_meta": 0,
#         "skipped_inline": 0,
#         "skipped_no_bytes": 0,
#         "errors": 0,
#     }

#     try:
#         atts = fetch_attachments(mailbox, graph_message_id)
#     except Exception as e:
#         audit_print(
#             "poller.attachments_fetch_error",
#             {"mailbox": mailbox, "email_id": email_id, "message_id": graph_message_id, "error": str(e)},
#         )
#         stats["errors"] += 1
#         return stats

#     stats["count"] = len(atts)
#     min_image_bytes = int(os.getenv("MIN_IMAGE_ATTACHMENT_BYTES", "102400"))

#     for a in atts:
#         try:
#             local_path = None

#             skip, reason = _should_skip_noise(a, min_image_bytes=min_image_bytes)
#             if skip:
#                 ops.upsert_email_attachment(email_id, a, None)
#                 stats["saved_meta"] += 1
#                 if reason == "inline":
#                     stats["skipped_inline"] += 1
#                 else:
#                     stats.setdefault("skipped_other", 0)
#                     stats["skipped_other"] += 1
#                 continue

#             if a.get("@odata.type") == "#microsoft.graph.fileAttachment":
#                 content_b64 = a.get("contentBytes")
#                 if not content_b64:
#                     ops.upsert_email_attachment(email_id, a, None)
#                     stats["saved_meta"] += 1
#                     stats["skipped_no_bytes"] += 1
#                     continue

#                 content_bytes = base64.b64decode("".join(str(content_b64).split()), validate=False)

#                 local_path = save_file_attachment(
#                     mailbox=mailbox,
#                     email_id=email_id,
#                     attachment=a,
#                     content_bytes=content_bytes,
#                 )
#                 stats["saved_files"] += 1

#             ops.upsert_email_attachment(email_id, a, local_path)
#             stats["saved_meta"] += 1

#         except Exception as e:
#             stats["errors"] += 1
#             audit_print(
#                 "poller.attachment_process_error",
#                 {"mailbox": mailbox, "email_id": email_id, "attachment_id": a.get("id"), "error": str(e)},
#             )

#     return stats


# def _normalize_pred_intent(llm_out: dict) -> tuple[str, float, str | None]:
#     pred_intent = (llm_out.get("intent") or "").strip()
#     try:
#         confidence = float(llm_out.get("confidence") or 0.0)
#     except Exception:
#         confidence = 0.0
#     recommended_status = llm_out.get("recommended_status")

#     # normalize recommended_status
#     if isinstance(recommended_status, str):
#         rs = recommended_status.strip()
#         if rs.lower() == "new":
#             recommended_status = None
#         else:
#             recommended_status = rs

#     # never apply status for noise intents
#     if pred_intent in {"non_case_email", "unknown", ""}:
#         recommended_status = None

#     return pred_intent, confidence, recommended_status


# def _strip_subject_header(draft_text: str) -> str:
#     if not draft_text:
#         return ""
#     lines = draft_text.splitlines()
#     if lines and lines[0].strip().lower().startswith("subject:"):
#         lines = lines[1:]
#         if lines and lines[0].strip() == "":
#             lines = lines[1:]
#     return "\n".join(lines).strip()


# def _text_to_simple_html(text: str) -> str:
#     text = (text or "").strip()
#     escaped = html.escape(text)
#     return "<div>" + escaped.replace("\n", "<br>") + "</div>"


# def _extract_staffing_fields(llm_out: dict) -> dict:
#     """
#     Pull likely staffing fields from LLM extracted object.
#     Supports multiple possible key names.
#     """
#     extracted = llm_out.get("extracted")
#     if not isinstance(extracted, dict):
#         return {}

#     def pick(*keys: str):
#         for k in keys:
#             v = extracted.get(k)
#             if isinstance(v, str) and v.strip():
#                 return v.strip()
#         return None

#     return {
#         "therapist_name": pick("therapist_name", "assigned_therapist", "therapist"),
#         "discipline": pick("discipline", "discipline_requested", "service", "therapy_type"),
#         "availability": pick("availability", "therapist_availability", "start_date", "requested_start_date"),
#         "referral_email": pick("referral_email", "referral_source_email", "contact_email"),
#     }


# def _maybe_auto_create_acceptance_draft(
#     *,
#     ops: MysqlOps,
#     case_id: int,
#     pred_intent: str,
#     confidence: float,
#     min_conf: float,
#     llm_out: dict,
# ) -> None:
#     """
#     If staffing confirmed and case is staffed, automatically create an acceptance draft in Outlook (Graph)
#     replying to the case seed email, store draft in DB, update status, and log event.
#     """
#     if pred_intent != "staffing_confirmation" or confidence < min_conf:
#         return

#     c = ops.get_case_by_id(int(case_id))
#     if not c:
#         return

#     current = (c.status or "").strip().lower()
#     if current in {"acceptance drafted", "acceptance sent", "closed"}:
#         return

#     # Ensure case is staffed before drafting acceptance
#     if current != "staffed":
#         return

#     meta = c.metadata_json or {}
#     if not isinstance(meta, dict):
#         meta = {}

#     staffing_patch = _extract_staffing_fields(llm_out)
#     if staffing_patch:
#         ops.merge_case_metadata(int(case_id), {"staffing": staffing_patch})

#     # Always reload after merge
#     c = ops.get_case_by_id(int(case_id))
#     meta = c.metadata_json or {}
#     if not isinstance(meta, dict):
#         meta = {}

#     staffing = meta.get("staffing") if isinstance(meta.get("staffing"), dict) else {}
#     referral_email = (staffing or {}).get("referral_email")
#     therapist_name = (staffing or {}).get("therapist_name")
#     discipline = (staffing or {}).get("discipline")
#     availability = (staffing or {}).get("availability")

#     # Use seed email as the thread to reply to
#     seed_email_id = meta.get("seed_email_id")
#     email_id = int(seed_email_id) if seed_email_id else None
#     if not email_id:
#         latest = ops.get_latest_email_for_case(int(case_id))
#         email_id = int(latest.id) if latest else None
#     if not email_id:
#         return

#     # Dedup: only one acceptance draft per case/email
#     if ops.case_event_exists_any(case_id=int(case_id), email_id=int(email_id), event_type="acceptance_draft_created"):
#         return

#     email_row = ops.get_email_by_id(int(email_id))
#     if not email_row:
#         return

#     mailbox = (email_row.mailbox or "").strip()
#     message_id = (email_row.message_id or "").strip()
#     if not mailbox or not message_id:
#         return

#     # LLM acceptance draft text
#     draft_text, model = draft_case_acceptance(
#         case_title=c.title,
#         referral_source_email=referral_email,
#         therapist_name=therapist_name,
#         discipline=discipline,
#         availability=availability,
#     )

#     # Create Graph reply draft
#     graph_draft = create_reply_draft(mailbox=mailbox, message_id=message_id)
#     graph_draft_id = (graph_draft.get("id") or "").strip()
#     graph_weblink = (graph_draft.get("webLink") or "").strip() if isinstance(graph_draft.get("webLink"), str) else None
#     if not graph_draft_id:
#         return

#     body_text = _strip_subject_header(draft_text or "")
#     body_html = _text_to_simple_html(body_text)

#     # Force To to referral_email if known; else keep default reply recipients
#     to_list = [referral_email] if isinstance(referral_email, str) and referral_email.strip() else None

#     update_draft_message(
#         mailbox=mailbox,
#         draft_message_id=graph_draft_id,
#         body_html=body_html,
#         to_recipients=to_list,
#     )

#     # Store DB draft (with graph ids if supported)
#     try:
#         draft_id = ops.create_draft(
#             email_id=int(email_id),
#             draft=draft_text,
#             model=model,
#             tone="professional",
#             mailbox=mailbox,
#             graph_draft_message_id=graph_draft_id,
#             graph_draft_web_link=graph_weblink,
#         )
#     except TypeError:
#         draft_id = ops.create_draft(
#             email_id=int(email_id),
#             draft=draft_text,
#             model=model,
#             tone="professional",
#             mailbox=mailbox,
#         )

#     ops.update_case(int(case_id), {"status": "acceptance drafted"})

#     ops.create_case_event(
#         case_id=int(case_id),
#         email_id=int(email_id),
#         event_type="acceptance_draft_created",
#         actor="ai",
#         payload={
#             "draft_id": draft_id,
#             "model": model,
#             "referral_email": referral_email,
#             "graph_draft_message_id": graph_draft_id,
#             "graph_draft_web_link": graph_weblink,
#         },
#     )


# def run_once_for_mailbox(mailbox: str) -> dict:
#     ops = MysqlOps()
#     state = ops.get_sync_state(mailbox)
#     delta_link = state.delta_link if state else None
#     last_sync_iso = state.last_sync_iso if state else None

#     limit = int(os.getenv("GRAPH_FETCH_LIMIT", "10"))

#     msgs = []
#     new_delta = None

#     if delta_link:
#         msgs, new_delta = fetch_messages_delta_for_mailbox(mailbox, delta_link, top=limit)
#         mode = "delta"
#     elif last_sync_iso:
#         msgs = fetch_messages_since_iso_for_mailbox(mailbox, since_iso=last_sync_iso, top=limit)
#         mode = "since"
#     else:
#         # BASELINE (first ever run):
#         new_delta = prime_delta_cursor_for_mailbox(mailbox)
#         mode = "delta_primed"

#         lookback_hours = int(os.getenv("BASELINE_LOOKBACK_HOURS", "72"))
#         ingest_recent = (os.getenv("BASELINE_INGEST_RECENT", "1").strip().lower() not in {"0", "false", "no"})

#         if ingest_recent and lookback_hours > 0:
#             since_dt = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
#             since_iso = since_dt.isoformat().replace("+00:00", "Z")
#             msgs = fetch_messages_since_iso_for_mailbox(mailbox, since_iso=since_iso, top=limit)
#             mode = f"delta_primed+since_{lookback_hours}h"
#         else:
#             msgs = []

#     saved = 0
#     attachments_total = 0
#     attachments_saved_files = 0
#     attachments_saved_meta = 0
#     attachments_errors = 0

#     min_conf = float(os.getenv("INTENT_MIN_CONFIDENCE", "0.65"))

#     for raw in msgs:
#         if raw.get("@removed"):
#             continue

#         email = to_email_item(raw, mailbox)

#         # 1) Save email
#         email_id = ops.upsert_email(email)

#         # 1.1) Persist received_at
#         received_at = _parse_graph_dt(email.get("received_datetime"))
#         if received_at:
#             ops.set_email_received_at(int(email_id), received_at)

#         # 2) Mailbox-scoped case key
#         conversation_id = (email.get("conversation_id") or "").strip()
#         case_external_id = f"{mailbox}:{conversation_id}" if conversation_id else f"{mailbox}:email:{email_id}"

#         # 3) Create/get case and link email->case
#         case_id = ops.get_or_create_case_by_external_id(
#             external_id=case_external_id,
#             title=email.get("subject") or "(no subject)",
#             metadata={"mailbox": mailbox, "conversation_id": conversation_id, "seed_email_id": int(email_id)},
#         )
#         ops.set_email_case_id(int(email_id), int(case_id))
#         saved += 1

#         # 4) Attachments (store them first, no extraction)
#         if email.get("has_attachments") and email.get("message_id") and email_id:
#             st = _try_process_attachments(
#                 ops=ops,
#                 mailbox=mailbox,
#                 email_id=int(email_id),
#                 graph_message_id=str(email["message_id"]),
#             )
#             attachments_total += st["count"]
#             attachments_saved_files += st["saved_files"]
#             attachments_saved_meta += st["saved_meta"]
#             attachments_errors += st["errors"]

#         # 5) Build attachment list from DB (metadata only)
#         atts_for_email = ops.list_attachments_for_email(int(email_id))
#         att_payload = [
#             {
#                 "id": a.id,
#                 "attachment_id": a.attachment_id,
#                 "name": a.name,
#                 "content_type": a.content_type,
#                 "size": a.size,
#                 "is_inline": bool(a.is_inline),
#                 "content_id": a.content_id,
#                 "local_path": a.local_path,
#                 "openai_file_id": getattr(a, "openai_file_id", None),
#             }
#             for a in atts_for_email
#         ]

#         # 6) ALWAYS run LLM processing (classification + extraction)
#         llm_out = None
#         llm_model = None
#         try:
#             llm_out, llm_model = process_email_llm(
#                 mailbox=mailbox,
#                 subject=email.get("subject"),
#                 sender=email.get("sender"),
#                 body_html=email.get("body_html"),
#                 body_preview=email.get("body_preview"),
#                 attachments=att_payload,
#             )
#         except Exception as e:
#             audit_print(
#                 "poller.llm_process_error",
#                 {"mailbox": mailbox, "email_id": int(email_id), "case_id": int(case_id), "error": str(e)},
#             )
#             llm_out = {
#                 "intent": "unknown",
#                 "confidence": 0.0,
#                 "signals": ["llm_failed"],
#                 "extracted": None,
#                 "recommended_status": None,
#             }
#             llm_model = os.getenv("OPENAI_MODEL", "gpt-5-nano")

#         # 7) Always log LLM output (single canonical event per email)
#         if not ops.case_event_exists_any(case_id=int(case_id), email_id=int(email_id), event_type="llm_processed"):
#             ops.create_case_event(
#                 case_id=int(case_id),
#                 email_id=int(email_id),
#                 event_type="llm_processed",
#                 actor="ai",
#                 payload={
#                     "model": llm_model,
#                     "min_confidence": min_conf,
#                     "mailbox": mailbox,
#                     "subject": email.get("subject"),
#                     "sender": email.get("sender"),
#                     "llm": llm_out,
#                 },
#             )

#         # 7.1) Also log a milestone event (intent) so watcher can find meaningful events
#         pred_intent, confidence, recommended_status = _normalize_pred_intent(llm_out)

#         if pred_intent and pred_intent not in {"non_case_email", "unknown"} and confidence >= min_conf:
#             if not ops.case_event_exists_any(case_id=int(case_id), email_id=int(email_id), event_type=pred_intent):
#                 ops.create_case_event(
#                     case_id=int(case_id),
#                     email_id=int(email_id),
#                     event_type=pred_intent,
#                     actor="ai",
#                     payload={
#                         "model": llm_model,
#                         "confidence": confidence,
#                         "mailbox": mailbox,
#                         "subject": email.get("subject"),
#                         "sender": email.get("sender"),
#                     },
#                 )

#         # 8) Apply status transition if confident (mapping priority)
#         case_row = ops.get_case_by_id(int(case_id))
#         current_status = case_row.status if case_row else None

#         if pred_intent and pred_intent not in {"non_case_email", "unknown"} and confidence >= min_conf:
#             mapped = None
#             if can_apply_intent(current_status, pred_intent):
#                 mapped = status_for_intent(pred_intent)

#             if mapped:
#                 if isinstance(recommended_status, str) and normalize_status(recommended_status) == normalize_status(mapped):
#                     ops.update_case(int(case_id), {"status": normalize_status(recommended_status)})
#                 else:
#                     ops.update_case(int(case_id), {"status": mapped})
#             else:
#                 if isinstance(recommended_status, str) and recommended_status.strip():
#                     new_status = normalize_status(recommended_status.strip())
#                     if new_status != "new":
#                         ops.update_case(int(case_id), {"status": new_status})

#         # 9) Merge extracted data (if any) into case metadata
#         extracted = llm_out.get("extracted")
#         if isinstance(extracted, dict) and extracted:
#             ops.merge_case_metadata(int(case_id), {"extracted": extracted})

#         # 10) NEW: if staffing_confirmation made the case staffed, auto-create acceptance draft in Outlook
#         try:
#             _maybe_auto_create_acceptance_draft(
#                 ops=ops,
#                 case_id=int(case_id),
#                 pred_intent=pred_intent,
#                 confidence=confidence,
#                 min_conf=min_conf,
#                 llm_out=llm_out,
#             )
#         except Exception as e:
#             audit_print(
#                 "poller.auto_acceptance_draft_error",
#                 {"mailbox": mailbox, "email_id": int(email_id), "case_id": int(case_id), "error": str(e)},
#             )

#     ops.upsert_sync_state(mailbox, new_delta or delta_link, now_iso())

#     audit_print(
#         "poller.run_once",
#         {
#             "mailbox": mailbox,
#             "mode": mode,
#             "fetched": len(msgs),
#             "saved": saved,
#             "has_new_delta": bool(new_delta and new_delta != delta_link),
#             "attachments_total": attachments_total,
#             "attachments_saved_files": attachments_saved_files,
#             "attachments_saved_meta": attachments_saved_meta,
#             "attachments_errors": attachments_errors,
#         },
#     )

#     return {
#         "mailbox": mailbox,
#         "mode": mode,
#         "fetched": len(msgs),
#         "saved": saved,
#         "has_new_delta": bool(new_delta and new_delta != delta_link),
#         "attachments_total": attachments_total,
#         "attachments_saved_files": attachments_saved_files,
#         "attachments_saved_meta": attachments_saved_meta,
#         "attachments_errors": attachments_errors,
#     }


# def run_once() -> dict:
#     mailboxes = _get_mailboxes()
#     if not mailboxes:
#         raise RuntimeError("No mailbox configured. Set MAILBOXES or MS_USER_ID in .env")

#     results = []
#     for m in mailboxes:
#         try:
#             results.append(run_once_for_mailbox(m))
#         except Exception as e:
#             audit_print("poller.mailbox_error", {"mailbox": m, "error": str(e)})
#     return {"items": results}


# def run_forever() -> None:
#     interval = int(os.getenv("POLL_INTERVAL_SECONDS", "30"))
#     while True:
#         try:
#             run_once()
#         except Exception as e:
#             audit_print("poller.error", {"error": str(e)})
#         time.sleep(interval)


# if __name__ == "__main__":
#     run_forever()




from __future__ import annotations

import os
import time
import base64
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
load_dotenv()

from app.core.audit import audit_print
from app.graph.mail import (
    fetch_messages_delta_for_mailbox,
    fetch_messages_since_iso_for_mailbox,
    prime_delta_cursor_for_mailbox,
    to_email_item,
    now_iso,
)

from app.graph.attachments import fetch_attachments, fetch_attachment_bytes
from app.storage.attachments import save_file_attachment
from app.mysql_ops import MysqlOps
from app.ai.tasks import process_email_llm
from app.core.intent_rules import can_apply_intent, status_for_intent
from app.core.status_rules import normalize_status

# NEW: auto-acceptance draft when staffing confirmed
from app.ai.tasks import draft_case_acceptance
from app.graph.reply import create_reply_draft, update_draft_message
import html


def _parse_graph_dt(dt_str: str | None):
    if not dt_str:
        return None
    try:
        if dt_str.endswith("Z"):
            dt_str = dt_str.replace("Z", "+00:00")
        return datetime.fromisoformat(dt_str)
    except Exception:
        return None


def _is_image_attachment(a: dict) -> bool:
    ct = (a.get("contentType") or "").lower()
    name = (a.get("name") or "").lower()
    return ct.startswith("image/") or name.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico"))


def _should_skip_noise(a: dict, min_image_bytes: int) -> tuple[bool, str]:
    if a.get("isInline") or a.get("contentId"):
        return True, "inline"

    if _is_image_attachment(a):
        size = int(a.get("size") or 0)
        if size and size < min_image_bytes:
            return True, f"small_image<{min_image_bytes}"

    return False, ""


def _get_mailboxes() -> list[str]:
    mailboxes = os.getenv("MAILBOXES", "").strip()
    if mailboxes:
        return [m.strip() for m in mailboxes.split(",") if m.strip()]
    single = os.getenv("MS_USER_ID", "").strip()
    if single:
        return [single]
    return []


def _try_process_attachments(
    ops: MysqlOps,
    mailbox: str,
    email_id: int,
    graph_message_id: str,
) -> dict:
    stats = {
        "count": 0,
        "saved_files": 0,
        "saved_meta": 0,
        "skipped_inline": 0,
        "skipped_no_bytes": 0,
        "errors": 0,
    }

    try:
        atts = fetch_attachments(mailbox, graph_message_id)
    except Exception as e:
        audit_print(
            "poller.attachments_fetch_error",
            {"mailbox": mailbox, "email_id": email_id, "message_id": graph_message_id, "error": str(e)},
        )
        stats["errors"] += 1
        return stats

    stats["count"] = len(atts)
    min_image_bytes = int(os.getenv("MIN_IMAGE_ATTACHMENT_BYTES", "102400"))

    try:
        from app.graph.attachments import fetch_attachment_bytes
    except Exception:
        fetch_attachment_bytes = None  # type: ignore

    for a in atts:
        try:
            local_path = None

            skip, reason = _should_skip_noise(a, min_image_bytes=min_image_bytes)
            if skip:
                ops.upsert_email_attachment(email_id, a, None)
                stats["saved_meta"] += 1
                if reason == "inline":
                    stats["skipped_inline"] += 1
                else:
                    stats.setdefault("skipped_other", 0)
                    stats["skipped_other"] += 1
                continue

            otype = (a.get("@odata.type") or "").strip()
            name_l = (a.get("name") or "").strip().lower()
            att_id = (a.get("id") or "").strip()

            # Treat as fileAttachment if:
            # - explicit fileAttachment
            # - OR type missing but it looks like a normal attachment (has id + name)
            is_file = (otype == "#microsoft.graph.fileAttachment") or (not otype and att_id and name_l)

            if is_file:
                content_bytes = None

                # 1) inline contentBytes (rare in list responses)
                content_b64 = a.get("contentBytes")
                if content_b64:
                    content_bytes = base64.b64decode("".join(str(content_b64).split()), validate=False)
                else:
                    # 2) fallback: download raw bytes via /$value
                    if fetch_attachment_bytes and att_id:
                        try:
                            content_bytes = fetch_attachment_bytes(mailbox, graph_message_id, att_id)
                        except Exception as e:
                            audit_print(
                                "poller.attachment_value_fetch_error",
                                {
                                    "mailbox": mailbox,
                                    "email_id": email_id,
                                    "message_id": graph_message_id,
                                    "attachment_id": att_id,
                                    "error": str(e),
                                },
                            )
                            content_bytes = None

                if not content_bytes:
                    ops.upsert_email_attachment(email_id, a, None)
                    stats["saved_meta"] += 1
                    stats["skipped_no_bytes"] += 1
                    continue

                local_path = save_file_attachment(
                    mailbox=mailbox,
                    email_id=email_id,
                    attachment=a,
                    content_bytes=content_bytes,
                )
                stats["saved_files"] += 1

            ops.upsert_email_attachment(email_id, a, local_path)
            stats["saved_meta"] += 1

        except Exception as e:
            stats["errors"] += 1
            audit_print(
                "poller.attachment_process_error",
                {"mailbox": mailbox, "email_id": email_id, "attachment_id": a.get("id"), "error": str(e)},
            )

    return stats

def _normalize_pred_intent(llm_out: dict) -> tuple[str, float, str | None]:
    pred_intent = (llm_out.get("intent") or "").strip()
    try:
        confidence = float(llm_out.get("confidence") or 0.0)
    except Exception:
        confidence = 0.0
    recommended_status = llm_out.get("recommended_status")

    # normalize recommended_status
    if isinstance(recommended_status, str):
        rs = recommended_status.strip()
        if rs.lower() == "new":
            recommended_status = None
        else:
            recommended_status = rs

    # never apply status for noise intents
    if pred_intent in {"non_case_email", "unknown", ""}:
        recommended_status = None

    return pred_intent, confidence, recommended_status


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


def _extract_staffing_fields(llm_out: dict) -> dict:
    """
    Pull likely staffing fields from LLM extracted object.
    Supports multiple possible key names.
    """
    extracted = llm_out.get("extracted")
    if not isinstance(extracted, dict):
        return {}

    def pick(*keys: str):
        for k in keys:
            v = extracted.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
        return None

    return {
        "therapist_name": pick("therapist_name", "assigned_therapist", "therapist"),
        "discipline": pick("discipline", "discipline_requested", "service", "therapy_type"),
        "availability": pick("availability", "therapist_availability", "start_date", "requested_start_date"),
        "referral_email": pick("referral_email", "referral_source_email", "contact_email"),
    }


def _maybe_auto_create_acceptance_draft(
    *,
    ops: MysqlOps,
    case_id: int,
    pred_intent: str,
    confidence: float,
    min_conf: float,
    llm_out: dict,
) -> None:
    """
    If staffing confirmed and case is staffed, automatically create an acceptance draft in Outlook (Graph)
    replying to the case seed email, store draft in DB, update status, and log event.
    """
    if pred_intent != "staffing_confirmation" or confidence < min_conf:
        return

    c = ops.get_case_by_id(int(case_id))
    if not c:
        return

    current = (c.status or "").strip().lower()
    if current in {"acceptance drafted", "acceptance sent", "closed"}:
        return

    # Ensure case is staffed before drafting acceptance
    if current != "staffed":
        return

    meta = c.metadata_json or {}
    if not isinstance(meta, dict):
        meta = {}

    staffing_patch = _extract_staffing_fields(llm_out)
    if staffing_patch:
        ops.merge_case_metadata(int(case_id), {"staffing": staffing_patch})

    # Always reload after merge
    c = ops.get_case_by_id(int(case_id))
    meta = c.metadata_json or {}
    if not isinstance(meta, dict):
        meta = {}

    staffing = meta.get("staffing") if isinstance(meta.get("staffing"), dict) else {}
    referral_email = (staffing or {}).get("referral_email")
    therapist_name = (staffing or {}).get("therapist_name")
    discipline = (staffing or {}).get("discipline")
    availability = (staffing or {}).get("availability")

    # Use seed email as the thread to reply to
    seed_email_id = meta.get("seed_email_id")
    email_id = int(seed_email_id) if seed_email_id else None
    if not email_id:
        latest = ops.get_latest_email_for_case(int(case_id))
        email_id = int(latest.id) if latest else None
    if not email_id:
        return

    # Dedup: only one acceptance draft per case/email
    if ops.case_event_exists_any(case_id=int(case_id), email_id=int(email_id), event_type="acceptance_draft_created"):
        return

    email_row = ops.get_email_by_id(int(email_id))
    if not email_row:
        return

    mailbox = (email_row.mailbox or "").strip()
    message_id = (email_row.message_id or "").strip()
    if not mailbox or not message_id:
        return

    # LLM acceptance draft text
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
        return

    body_text = _strip_subject_header(draft_text or "")
    body_html = _text_to_simple_html(body_text)

    # Force To to referral_email if known; else keep default reply recipients
    to_list = [referral_email] if isinstance(referral_email, str) and referral_email.strip() else None

    update_draft_message(
        mailbox=mailbox,
        draft_message_id=graph_draft_id,
        body_html=body_html,
        to_recipients=to_list,
    )

    # Store DB draft (with graph ids if supported)
    try:
        draft_id = ops.create_draft(
            email_id=int(email_id),
            draft=draft_text,
            model=model,
            tone="professional",
            mailbox=mailbox,
            graph_draft_message_id=graph_draft_id,
            graph_draft_web_link=graph_weblink,
        )
    except TypeError:
        draft_id = ops.create_draft(
            email_id=int(email_id),
            draft=draft_text,
            model=model,
            tone="professional",
            mailbox=mailbox,
        )

    ops.update_case(int(case_id), {"status": "acceptance drafted"})

    ops.create_case_event(
        case_id=int(case_id),
        email_id=int(email_id),
        event_type="acceptance_draft_created",
        actor="ai",
        payload={
            "draft_id": draft_id,
            "model": model,
            "referral_email": referral_email,
            "graph_draft_message_id": graph_draft_id,
            "graph_draft_web_link": graph_weblink,
        },
    )


def run_once_for_mailbox(mailbox: str) -> dict:
    ops = MysqlOps()
    state = ops.get_sync_state(mailbox)
    delta_link = state.delta_link if state else None
    last_sync_iso = state.last_sync_iso if state else None

    limit = int(os.getenv("GRAPH_FETCH_LIMIT", "10"))

    msgs = []
    new_delta = None

    if delta_link:
        msgs, new_delta = fetch_messages_delta_for_mailbox(mailbox, delta_link, top=limit)
        mode = "delta"
    elif last_sync_iso:
        msgs = fetch_messages_since_iso_for_mailbox(mailbox, since_iso=last_sync_iso, top=limit)
        mode = "since"
    else:
        # BASELINE (first ever run):
        new_delta = prime_delta_cursor_for_mailbox(mailbox)
        mode = "delta_primed"

        lookback_hours = int(os.getenv("BASELINE_LOOKBACK_HOURS", "72"))
        ingest_recent = (os.getenv("BASELINE_INGEST_RECENT", "1").strip().lower() not in {"0", "false", "no"})

        if ingest_recent and lookback_hours > 0:
            since_dt = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
            since_iso = since_dt.isoformat().replace("+00:00", "Z")
            msgs = fetch_messages_since_iso_for_mailbox(mailbox, since_iso=since_iso, top=limit)
            mode = f"delta_primed+since_{lookback_hours}h"
        else:
            msgs = []

    saved = 0
    attachments_total = 0
    attachments_saved_files = 0
    attachments_saved_meta = 0
    attachments_errors = 0

    min_conf = float(os.getenv("INTENT_MIN_CONFIDENCE", "0.65"))

    for raw in msgs:
        if raw.get("@removed"):
            continue

        # ------------------------------------------------------------
        # FIX: Graph delta can return partial objects (id only).
        # These create "empty emails" in DB if we upsert them.
        # Skip anything that doesn't have receivedDateTime.
        # ------------------------------------------------------------
        if not raw.get("receivedDateTime"):
            audit_print(
                "poller.skip_partial_delta_item",
                {
                    "mailbox": mailbox,
                    "graph_id": raw.get("id"),
                    "keys": sorted(list(raw.keys()))[:40],
                },
            )
            continue

        email = to_email_item(raw, mailbox)

        # 1) Save email
        email_id = ops.upsert_email(email)

        # 1.1) Persist received_at
        received_at = _parse_graph_dt(email.get("received_datetime"))
        if received_at:
            ops.set_email_received_at(int(email_id), received_at)

        # 2) Mailbox-scoped case key
        conversation_id = (email.get("conversation_id") or "").strip()
        case_external_id = f"{mailbox}:{conversation_id}" if conversation_id else f"{mailbox}:email:{email_id}"

        # 3) Create/get case and link email->case
        case_id = ops.get_or_create_case_by_external_id(
            external_id=case_external_id,
            title=email.get("subject") or "(no subject)",
            metadata={"mailbox": mailbox, "conversation_id": conversation_id, "seed_email_id": int(email_id)},
        )
        ops.set_email_case_id(int(email_id), int(case_id))
        saved += 1

        # 4) Attachments (store them first, no extraction)
        if email.get("has_attachments") and email.get("message_id") and email_id:
            st = _try_process_attachments(
                ops=ops,
                mailbox=mailbox,
                email_id=int(email_id),
                graph_message_id=str(email["message_id"]),
            )
            attachments_total += st["count"]
            attachments_saved_files += st["saved_files"]
            attachments_saved_meta += st["saved_meta"]
            attachments_errors += st["errors"]

        # 5) Build attachment list from DB (metadata only)
        atts_for_email = ops.list_attachments_for_email(int(email_id))
        att_payload = [
            {
                "id": a.id,
                "attachment_id": a.attachment_id,
                "name": a.name,
                "content_type": a.content_type,
                "size": a.size,
                "is_inline": bool(a.is_inline),
                "content_id": a.content_id,
                "local_path": a.local_path,
                "openai_file_id": getattr(a, "openai_file_id", None),
            }
            for a in atts_for_email
        ]

        # 6) ALWAYS run LLM processing (classification + extraction)
        llm_out = None
        llm_model = None
        try:
            llm_out, llm_model = process_email_llm(
                mailbox=mailbox,
                subject=email.get("subject"),
                sender=email.get("sender"),
                body_html=email.get("body_html"),
                body_preview=email.get("body_preview"),
                attachments=att_payload,
            )
        except Exception as e:
            audit_print(
                "poller.llm_process_error",
                {"mailbox": mailbox, "email_id": int(email_id), "case_id": int(case_id), "error": str(e)},
            )
            llm_out = {
                "intent": "unknown",
                "confidence": 0.0,
                "signals": ["llm_failed"],
                "extracted": None,
                "recommended_status": None,
            }
            llm_model = os.getenv("OPENAI_MODEL", "gpt-5-nano")

        # 7) Always log LLM output (single canonical event per email)
        if not ops.case_event_exists_any(case_id=int(case_id), email_id=int(email_id), event_type="llm_processed"):
            ops.create_case_event(
                case_id=int(case_id),
                email_id=int(email_id),
                event_type="llm_processed",
                actor="ai",
                payload={
                    "model": llm_model,
                    "min_confidence": min_conf,
                    "mailbox": mailbox,
                    "subject": email.get("subject"),
                    "sender": email.get("sender"),
                    "llm": llm_out,
                },
            )

        # 7.1) Also log a milestone event (intent) so watcher can find meaningful events
        pred_intent, confidence, recommended_status = _normalize_pred_intent(llm_out)

        if pred_intent and pred_intent not in {"non_case_email", "unknown"} and confidence >= min_conf:
            if not ops.case_event_exists_any(case_id=int(case_id), email_id=int(email_id), event_type=pred_intent):
                ops.create_case_event(
                    case_id=int(case_id),
                    email_id=int(email_id),
                    event_type=pred_intent,
                    actor="ai",
                    payload={
                        "model": llm_model,
                        "confidence": confidence,
                        "mailbox": mailbox,
                        "subject": email.get("subject"),
                        "sender": email.get("sender"),
                    },
                )

        # 8) Apply status transition if confident (mapping priority)
        case_row = ops.get_case_by_id(int(case_id))
        current_status = case_row.status if case_row else None

        if pred_intent and pred_intent not in {"non_case_email", "unknown"} and confidence >= min_conf:
            mapped = None
            if can_apply_intent(current_status, pred_intent):
                mapped = status_for_intent(pred_intent)

            if mapped:
                if isinstance(recommended_status, str) and normalize_status(recommended_status) == normalize_status(mapped):
                    ops.update_case(int(case_id), {"status": normalize_status(recommended_status)})
                else:
                    ops.update_case(int(case_id), {"status": mapped})
            else:
                if isinstance(recommended_status, str) and recommended_status.strip():
                    new_status = normalize_status(recommended_status.strip())
                    if new_status != "new":
                        ops.update_case(int(case_id), {"status": new_status})

        # 9) Merge extracted data (if any) into case metadata
        extracted = llm_out.get("extracted")
        if isinstance(extracted, dict) and extracted:
            ops.merge_case_metadata(int(case_id), {"extracted": extracted})

        # 10) NEW: if staffing_confirmation made the case staffed, auto-create acceptance draft in Outlook
        try:
            _maybe_auto_create_acceptance_draft(
                ops=ops,
                case_id=int(case_id),
                pred_intent=pred_intent,
                confidence=confidence,
                min_conf=min_conf,
                llm_out=llm_out,
            )
        except Exception as e:
            audit_print(
                "poller.auto_acceptance_draft_error",
                {"mailbox": mailbox, "email_id": int(email_id), "case_id": int(case_id), "error": str(e)},
            )

    ops.upsert_sync_state(mailbox, new_delta or delta_link, now_iso())

    audit_print(
        "poller.run_once",
        {
            "mailbox": mailbox,
            "mode": mode,
            "fetched": len(msgs),
            "saved": saved,
            "has_new_delta": bool(new_delta and new_delta != delta_link),
            "attachments_total": attachments_total,
            "attachments_saved_files": attachments_saved_files,
            "attachments_saved_meta": attachments_saved_meta,
            "attachments_errors": attachments_errors,
        },
    )

    return {
        "mailbox": mailbox,
        "mode": mode,
        "fetched": len(msgs),
        "saved": saved,
        "has_new_delta": bool(new_delta and new_delta != delta_link),
        "attachments_total": attachments_total,
        "attachments_saved_files": attachments_saved_files,
        "attachments_saved_meta": attachments_saved_meta,
        "attachments_errors": attachments_errors,
    }


def run_once() -> dict:
    mailboxes = _get_mailboxes()
    if not mailboxes:
        raise RuntimeError("No mailbox configured. Set MAILBOXES or MS_USER_ID in .env")

    results = []
    for m in mailboxes:
        try:
            results.append(run_once_for_mailbox(m))
        except Exception as e:
            audit_print("poller.mailbox_error", {"mailbox": m, "error": str(e)})
    return {"items": results}


def run_forever() -> None:
    interval = int(os.getenv("POLL_INTERVAL_SECONDS", "30"))
    while True:
        try:
            run_once()
        except Exception as e:
            audit_print("poller.error", {"error": str(e)})
        time.sleep(interval)


if __name__ == "__main__":
    run_forever()
