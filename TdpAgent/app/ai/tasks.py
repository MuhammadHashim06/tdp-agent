# # app/ai/tasks.py  (FIXED ImportError + draft_case_acceptance implemented)
# from __future__ import annotations

# import os
# import json
# from dotenv import load_dotenv

# from app.ai.client import get_openai_client
# from app.ai.prompts import (
#     SYSTEM_DRAFT,
#     user_prompt_for_draft,
#     SYSTEM_ACCEPTANCE,
#     user_prompt_for_acceptance,
#     SYSTEM_REFERRAL_EXTRACT,
#     user_prompt_for_referral_extract,
#     SYSTEM_INTENT_CLASSIFIER,
#     user_prompt_for_intent_classification,
#     SYSTEM_EMAIL_PROCESSOR,
#     user_prompt_for_email_processing,
# )
# from app.core.sanitize import strip_html, safe_text
# from app.ai.schemas import ReferralExtractOut, IntentClassifyOut

# load_dotenv()

# ALLOWED_INTENTS_DEFAULT = [
#     "referral_received",
#     "evaluation_received",
#     "authorization_approved",
#     "authorization_request",
#     "staffing_confirmation",
#     "non_case_email",
#     "unknown",
# ]

# ALLOWED_STATUSES_DEFAULT = [
#     "new",
#     "pending staffing",
#     "staffed",
#     "acceptance drafted",
#     "acceptance sent",
#     "evaluation completed",
#     "authorization pending",
#     "authorized – treatment started",
#     "closed",
# ]


# def _coerce_body_text(body_html: str | None, body_preview: str | None) -> str:
#     body_text = body_preview or ""
#     if body_html:
#         body_text = strip_html(body_html) or body_text
#     return safe_text(body_text, 12000)


# def _response_text(resp) -> str:
#     txt = getattr(resp, "output_text", None)
#     if isinstance(txt, str) and txt.strip():
#         return txt.strip()

#     out = getattr(resp, "output", None)
#     if isinstance(out, list):
#         parts = []
#         for item in out:
#             content = item.get("content") if isinstance(item, dict) else getattr(item, "content", None)
#             if isinstance(content, list):
#                 for c in content:
#                     t = c.get("text") if isinstance(c, dict) else getattr(c, "text", None)
#                     if t:
#                         parts.append(t)
#         return "\n".join(parts).strip()

#     return ""


# # --------------------------------------------------------------------------------------
# # Attachments → OpenAI (as-is)
# # --------------------------------------------------------------------------------------

# def _upload_openai_file(local_path: str) -> str:
#     client = get_openai_client()
#     purpose = (os.getenv("OPENAI_FILE_PURPOSE", "user_data") or "user_data").strip()
#     with open(local_path, "rb") as f:
#         up = client.files.create(file=f, purpose=purpose)
#     return up.id


# def _responses_create_json(client, *, model: str, system_text: str, user_text: str, file_ids: list[str]):
#     base = {
#         "model": model,
#         "input": [
#             {"role": "system", "content": [{"type": "input_text", "text": system_text}]},
#             {
#                 "role": "user",
#                 "content": (
#                     [{"type": "input_text", "text": user_text}]
#                     + [{"type": "input_file", "file_id": fid} for fid in (file_ids or [])]
#                 ),
#             },
#         ],
#     }

#     try:
#         return client.responses.create(
#             **base,
#             text={"format": {"type": "json_object"}},
#         )
#     except TypeError:
#         return client.responses.create(**base)


# def _responses_create_text(client, *, model: str, system_text: str, user_text: str, file_ids: list[str] | None = None):
#     base = {
#         "model": model,
#         "input": [
#             {"role": "system", "content": [{"type": "input_text", "text": system_text}]},
#             {
#                 "role": "user",
#                 "content": (
#                     [{"type": "input_text", "text": user_text}]
#                     + [{"type": "input_file", "file_id": fid} for fid in (file_ids or [])]
#                 ),
#             },
#         ],
#     }
#     return client.responses.create(**base)


# def process_email_llm(
#     *,
#     mailbox: str,
#     subject: str | None,
#     sender: str | None,
#     body_html: str | None,
#     body_preview: str | None,
#     attachments: list[dict] | None,
#     allowed_intents: list[str] | None = None,
#     allowed_statuses: list[str] | None = None,
# ) -> tuple[dict, str]:

#     allowed_i = allowed_intents or ALLOWED_INTENTS_DEFAULT
#     allowed_s = allowed_statuses or ALLOWED_STATUSES_DEFAULT

#     body_text = safe_text(_coerce_body_text(body_html, body_preview), 12000)
#     subject_s = safe_text(subject or "", 300)
#     sender_s = safe_text(sender or "", 300)
#     mailbox_s = safe_text(mailbox or "", 200)

#     file_ids: list[str] = []
#     upload_failures: list[str] = []

#     try:
#         from app.mysql_ops import MysqlOps
#         ops = MysqlOps()
#     except Exception:
#         ops = None

#     for a in attachments or []:
#         try:
#             local_path = (a.get("local_path") or "").strip()
#             if not local_path:
#                 continue

#             cached = (a.get("openai_file_id") or "").strip()
#             if cached:
#                 file_ids.append(cached)
#                 continue

#             fid = _upload_openai_file(local_path)
#             file_ids.append(fid)

#             if ops and a.get("id"):
#                 try:
#                     ops.set_attachment_openai_file_id(int(a["id"]), fid)
#                 except Exception:
#                     pass

#         except Exception as e:
#             upload_failures.append(f"id={a.get('id')} err={type(e).__name__}")

#     client = get_openai_client()
#     model = os.getenv("OPENAI_MODEL", "gpt-5-nano")

#     prompt = user_prompt_for_email_processing(
#         mailbox=mailbox_s,
#         subject=subject_s,
#         sender=sender_s,
#         body_text=body_text,
#         allowed_intents=allowed_i,
#         allowed_statuses=allowed_s,
#     )

#     resp = _responses_create_json(
#         client,
#         model=model,
#         system_text=SYSTEM_EMAIL_PROCESSOR,
#         user_text=prompt,
#         file_ids=file_ids,
#     )

#     raw = _response_text(resp)

#     try:
#         out = json.loads(raw)
#     except Exception:
#         out = {
#             "intent": "unknown",
#             "confidence": 0.0,
#             "signals": ["json_parse_failed"],
#             "extracted": None,
#             "recommended_status": None,
#         }

#     if file_ids:
#         out["signals"] = (out.get("signals") or []) + ["files_attached"]

#     if upload_failures:
#         out["signals"] = (out.get("signals") or []) + ["attachment_upload_failed"]
#         out["attachment_upload_failures"] = upload_failures[:5]

#     if out.get("intent") not in allowed_i:
#         out["intent"] = "unknown"
#         out["confidence"] = 0.0
#         out["signals"] = (out.get("signals") or []) + ["intent_not_allowed"]

#     if out.get("recommended_status") not in allowed_s:
#         out["recommended_status"] = None

#     out.setdefault("confidence", 0.0)
#     out.setdefault("signals", [])
#     out.setdefault("extracted", None)
#     out.setdefault("recommended_status", None)

#     return out, model


# # --------------------------------------------------------------------------------------
# # FIX: add draft_case_acceptance for API import (cases.py)
# # Uses Responses API (no temperature, no response_format kwargs)
# # --------------------------------------------------------------------------------------

# def draft_case_acceptance(
#     *,
#     case_title: str,
#     referral_source_email: str | None,
#     therapist_name: str | None,
#     discipline: str | None,
#     availability: str | None,
# ) -> tuple[str, str]:
#     client = get_openai_client()
#     model = os.getenv("OPENAI_MODEL", "gpt-5-nano")

#     prompt = user_prompt_for_acceptance(
#         case_title=safe_text(case_title or "", 400),
#         referral_source_email=safe_text(referral_source_email or "", 300),
#         therapist_name=safe_text(therapist_name or "", 200),
#         discipline=safe_text(discipline or "", 200),
#         availability=safe_text(availability or "", 400),
#     )

#     resp = _responses_create_text(
#         client,
#         model=model,
#         system_text=SYSTEM_ACCEPTANCE,
#         user_text=prompt,
#         file_ids=[],
#     )

#     draft_text = _response_text(resp).strip()
#     if not draft_text:
#         draft_text = "Thank you. We can accept the case. Please confirm the next steps and scheduling details."

#     return draft_text, model

# def draft_reply(
#     *,
#     subject: str | None = None,
#     sender: str | None = None,
#     body_html: str | None = None,
#     body_preview: str | None = None,
#     tone: str | None = "professional",
#     instructions: str | None = None,
# ) -> tuple[str, str]:
#     """
#     Generates a reply draft for an email thread.
#     Uses Responses API (works with gpt-5-nano; no temperature/response_format kwargs).
#     Returns: (draft_text, model)
#     """
#     client = get_openai_client()
#     model = os.getenv("OPENAI_MODEL", "gpt-5-nano")

#     body_text = safe_text(_coerce_body_text(body_html, body_preview), 12000)

#     prompt = user_prompt_for_draft(
#         subject=safe_text(subject or "", 300),
#         sender=safe_text(sender or "", 300),
#         body_text=body_text,
#         tone=safe_text(tone or "professional", 50),
#         instructions=safe_text(instructions or "", 1000) if instructions else None,
#     )

#     resp = _responses_create_text(
#         client,
#         model=model,
#         system_text=SYSTEM_DRAFT,
#         user_text=prompt,
#         file_ids=[],
#     )

#     draft_text = _response_text(resp).strip()
#     if not draft_text:
#         draft_text = "Thanks for the update. We will review and follow up with next steps."
#     return draft_text, model























































































# # app/ai/tasks.py
# from __future__ import annotations

# import os
# import json
# import base64
# from typing import Any

# from dotenv import load_dotenv

# from app.ai.client import get_openai_client
# from app.ai.prompts import (
#     SYSTEM_DRAFT,
#     user_prompt_for_draft,
#     SYSTEM_ACCEPTANCE,
#     user_prompt_for_acceptance,
#     SYSTEM_REFERRAL_EXTRACT,
#     user_prompt_for_referral_extract,
#     SYSTEM_INTENT_CLASSIFIER,
#     user_prompt_for_intent_classification,
#     SYSTEM_EMAIL_PROCESSOR,
#     user_prompt_for_email_processing,
# )
# from app.core.sanitize import strip_html, safe_text
# from app.ai.schemas import ReferralExtractOut, IntentClassifyOut

# load_dotenv()

# ALLOWED_INTENTS_DEFAULT = [
#     "referral_received",
#     "evaluation_received",
#     "authorization_approved",
#     "authorization_request",
#     "staffing_confirmation",
#     "non_case_email",
#     "unknown",
# ]

# ALLOWED_STATUSES_DEFAULT = [
#     "new",
#     "pending staffing",
#     "staffed",
#     "acceptance drafted",
#     "acceptance sent",
#     "evaluation completed",
#     "authorization pending",
#     "authorized – treatment started",
#     "closed",
# ]


# def _coerce_body_text(body_html: str | None, body_preview: str | None) -> str:
#     body_text = body_preview or ""
#     if body_html:
#         body_text = strip_html(body_html) or body_text
#     return safe_text(body_text, 12000)


# def _response_text(resp) -> str:
#     txt = getattr(resp, "output_text", None)
#     if isinstance(txt, str) and txt.strip():
#         return txt.strip()

#     out = getattr(resp, "output", None)
#     if isinstance(out, list):
#         parts = []
#         for item in out:
#             content = item.get("content") if isinstance(item, dict) else getattr(item, "content", None)
#             if isinstance(content, list):
#                 for c in content:
#                     t = c.get("text") if isinstance(c, dict) else getattr(c, "text", None)
#                     if t:
#                         parts.append(t)
#         return "\n".join(parts).strip()

#     return ""


# # --------------------------------------------------------------------------------------
# # Attachments → OpenAI (as-is)
# # --------------------------------------------------------------------------------------

# def _upload_openai_file(local_path: str) -> str:
#     client = get_openai_client()
#     purpose = (os.getenv("OPENAI_FILE_PURPOSE", "user_data") or "user_data").strip()
#     with open(local_path, "rb") as f:
#         up = client.files.create(file=f, purpose=purpose)
#     return up.id


# # --------------------------------------------------------------------------------------
# # PDF (scanned) → images (Option 2)
# # --------------------------------------------------------------------------------------

# def _is_pdf_attachment(a: dict) -> bool:
#     name = (a.get("name") or "").lower()
#     ct = (a.get("content_type") or a.get("contentType") or "").lower()
#     return name.endswith(".pdf") or ct in {"application/pdf", "application/x-pdf"}


# def _pdf_pages_to_png_b64(
#     local_path: str,
#     *,
#     dpi: int,
#     max_pages: int,
# ) -> list[dict]:
#     """
#     Render up to max_pages of a PDF to PNG images and return:
#     [{"page": 1, "b64": "...", "mime": "image/png"}...]
#     Uses PyMuPDF (fitz). If missing, returns [].
#     """
#     try:
#         import fitz  # pymupdf
#     except Exception:
#         return []

#     out: list[dict] = []
#     doc = None
#     try:
#         doc = fitz.open(local_path)
#         zoom = float(dpi) / 72.0
#         mat = fitz.Matrix(zoom, zoom)

#         total = int(getattr(doc, "page_count", 0) or 0)
#         n = min(total, int(max_pages))

#         for i in range(n):
#             page = doc.load_page(i)
#             pix = page.get_pixmap(matrix=mat, alpha=False)
#             png_bytes = pix.tobytes("png")
#             b64 = base64.b64encode(png_bytes).decode("ascii")
#             out.append({"page": i + 1, "b64": b64, "mime": "image/png"})
#     except Exception:
#         return []
#     finally:
#         try:
#             if doc is not None:
#                 doc.close()
#         except Exception:
#             pass

#     return out


# def _build_vision_images_from_attachments(attachments: list[dict] | None) -> list[dict]:
#     """
#     Returns list of {"attachment_id":..., "name":..., "page":..., "mime":..., "b64":...}
#     with hard caps to avoid token/payload blowups.
#     """
#     if not attachments:
#         return []

#     enabled = (os.getenv("PDF_VISION_ENABLED", "1").strip().lower() not in {"0", "false", "no"})
#     if not enabled:
#         return []

#     dpi = int(os.getenv("PDF_VISION_DPI", "180"))
#     max_pages_per_pdf = int(os.getenv("PDF_VISION_MAX_PAGES", "5"))
#     max_total_images = int(os.getenv("PDF_VISION_MAX_IMAGES", "10"))

#     images: list[dict] = []
#     for a in attachments:
#         if len(images) >= max_total_images:
#             break

#         local_path = (a.get("local_path") or "").strip()
#         if not local_path:
#             continue
#         if not _is_pdf_attachment(a):
#             continue

#         pages = _pdf_pages_to_png_b64(local_path, dpi=dpi, max_pages=max_pages_per_pdf)
#         for p in pages:
#             if len(images) >= max_total_images:
#                 break
#             images.append(
#                 {
#                     "attachment_id": a.get("attachment_id") or a.get("id"),
#                     "name": a.get("name"),
#                     "page": p["page"],
#                     "mime": p["mime"],
#                     "b64": p["b64"],
#                 }
#             )

#     return images


# def _responses_create_json(
#     client,
#     *,
#     model: str,
#     system_text: str,
#     user_text: str,
#     file_ids: list[str],
#     images: list[dict] | None = None,
# ):
#     user_content: list[dict] = [{"type": "input_text", "text": user_text}]

#     # Attach scanned-PDF pages as images (Option 2) - FIXED
#     for img in images or []:
#         mime = (img.get("mime") or "image/png").strip() or "image/png"
#         b64 = (img.get("b64") or "").strip()
#         if not b64:
#             continue
#         user_content.append(
#             {
#                 "type": "input_image",
#                 "image_url": f"data:{mime};base64,{b64}",
#             }
#         )

#     # Attach original files as-is (Option 1)
#     for fid in (file_ids or []):
#         user_content.append({"type": "input_file", "file_id": fid})

#     base = {
#         "model": model,
#         "input": [
#             {"role": "system", "content": [{"type": "input_text", "text": system_text}]},
#             {"role": "user", "content": user_content},
#         ],
#     }

#     try:
#         return client.responses.create(
#             **base,
#             text={"format": {"type": "json_object"}},
#         )
#     except TypeError:
#         return client.responses.create(**base)


# def _responses_create_text(
#     client,
#     *,
#     model: str,
#     system_text: str,
#     user_text: str,
#     file_ids: list[str] | None = None,
#     images: list[dict] | None = None,
# ):
#     user_content: list[dict] = [{"type": "input_text", "text": user_text}]

#     for img in images or []:
#         mime = (img.get("mime") or "image/png").strip() or "image/png"
#         b64 = (img.get("b64") or "").strip()
#         if not b64:
#             continue
#         user_content.append(
#             {
#                 "type": "input_image",
#                 "image_url": f"data:{mime};base64,{b64}",
#             }
#         )

#     for fid in (file_ids or []):
#         user_content.append({"type": "input_file", "file_id": fid})

#     base = {
#         "model": model,
#         "input": [
#             {"role": "system", "content": [{"type": "input_text", "text": system_text}]},
#             {"role": "user", "content": user_content},
#         ],
#     }
#     return client.responses.create(**base)


# def process_email_llm(
#     *,
#     mailbox: str,
#     subject: str | None,
#     sender: str | None,
#     body_html: str | None,
#     body_preview: str | None,
#     attachments: list[dict] | None,
#     allowed_intents: list[str] | None = None,
#     allowed_statuses: list[str] | None = None,
# ) -> tuple[dict, str]:
#     """
#     Unified classifier + extractor.
#     - Uploads attachments "as-is" (cached via openai_file_id).
#     - Additionally renders scanned PDF attachments into page images and sends as vision inputs.
#     """

#     allowed_i = allowed_intents or ALLOWED_INTENTS_DEFAULT
#     allowed_s = allowed_statuses or ALLOWED_STATUSES_DEFAULT

#     body_text = safe_text(_coerce_body_text(body_html, body_preview), 12000)
#     subject_s = safe_text(subject or "", 300)
#     sender_s = safe_text(sender or "", 300)
#     mailbox_s = safe_text(mailbox or "", 200)

#     desired_extract_keys = list(getattr(ReferralExtractOut, "model_fields", {}).keys()) or [
#         "patient_name",
#         "dob",
#         "diagnosis",
#         "address",
#         "insurance",
#         "discipline_requested",
#         "referral_source_name",
#         "referral_source_org",
#         "referral_source_email",
#         "referral_source_phone",
#         "referral_source_fax",
#         "patient_id",
#         "mrn",
#         "ordering_provider",
#         "requested_start_date",
#         "visit_frequency",
#         "authorization_required",
#         "language",
#         "caregiver_contact",
#         "special_instructions",
#         "extracted_from",
#         "confidence_notes",
#         "evidence",
#     ]

#     file_ids: list[str] = []
#     upload_failures: list[str] = []

#     try:
#         from app.mysql_ops import MysqlOps
#         ops = MysqlOps()
#     except Exception:
#         ops = None

#     vision_images = _build_vision_images_from_attachments(attachments or [])

#     for a in attachments or []:
#         try:
#             local_path = (a.get("local_path") or "").strip()
#             if not local_path:
#                 continue

#             cached = (a.get("openai_file_id") or "").strip()
#             if cached:
#                 file_ids.append(cached)
#                 continue

#             fid = _upload_openai_file(local_path)
#             file_ids.append(fid)

#             if ops and a.get("id"):
#                 try:
#                     ops.set_attachment_openai_file_id(int(a["id"]), fid)
#                 except Exception:
#                     pass

#         except Exception as e:
#             upload_failures.append(f"id={a.get('id')} err={type(e).__name__}")

#     client = get_openai_client()
#     model = os.getenv("OPENAI_MODEL", "gpt-5-nano")

#     prompt = user_prompt_for_email_processing(
#         mailbox=mailbox_s,
#         subject=subject_s,
#         sender=sender_s,
#         body_text=body_text,
#         allowed_intents=allowed_i,
#         allowed_statuses=allowed_s,
#     )

#     prompt += f"""

# Extraction requirements (IMPORTANT):
# - Many attachments are scanned PDFs. Use the attached images (rendered PDF pages) to extract patient/referral details.
# - Populate extracted with as many of these keys as you can find (use null if missing):
# {desired_extract_keys}

# Evidence requirement:
# - If you extract patient_name/dob/diagnosis/insurance/mrn, include short evidence snippets inside extracted.evidence when possible.
# """

#     resp = _responses_create_json(
#         client,
#         model=model,
#         system_text=SYSTEM_EMAIL_PROCESSOR,
#         user_text=prompt,
#         file_ids=file_ids,
#         images=vision_images,
#     )

#     raw = _response_text(resp)

#     try:
#         out = json.loads(raw)
#     except Exception:
#         out = {
#             "intent": "unknown",
#             "confidence": 0.0,
#             "signals": ["json_parse_failed"],
#             "extracted": None,
#             "recommended_status": None,
#         }

#     if file_ids:
#         out["signals"] = (out.get("signals") or []) + ["files_attached"]
#     if vision_images:
#         out["signals"] = (out.get("signals") or []) + [f"pdf_vision_images:{len(vision_images)}"]
#     if upload_failures:
#         out["signals"] = (out.get("signals") or []) + ["attachment_upload_failed"]
#         out["attachment_upload_failures"] = upload_failures[:5]

#     if out.get("intent") not in allowed_i:
#         out["intent"] = "unknown"
#         out["confidence"] = 0.0
#         out["signals"] = (out.get("signals") or []) + ["intent_not_allowed"]

#     if out.get("recommended_status") not in allowed_s:
#         out["recommended_status"] = None

#     out.setdefault("confidence", 0.0)
#     out.setdefault("signals", [])
#     out.setdefault("extracted", None)
#     out.setdefault("recommended_status", None)

#     return out, model


# def draft_case_acceptance(
#     *,
#     case_title: str,
#     referral_source_email: str | None,
#     therapist_name: str | None,
#     discipline: str | None,
#     availability: str | None,
# ) -> tuple[str, str]:
#     client = get_openai_client()
#     model = os.getenv("OPENAI_MODEL", "gpt-5-nano")

#     prompt = user_prompt_for_acceptance(
#         case_title=safe_text(case_title or "", 400),
#         referral_source_email=safe_text(referral_source_email or "", 300),
#         therapist_name=safe_text(therapist_name or "", 200),
#         discipline=safe_text(discipline or "", 200),
#         availability=safe_text(availability or "", 400),
#     )

#     resp = _responses_create_text(
#         client,
#         model=model,
#         system_text=SYSTEM_ACCEPTANCE,
#         user_text=prompt,
#         file_ids=[],
#         images=[],
#     )

#     draft_text = _response_text(resp).strip()
#     if not draft_text:
#         draft_text = "Thank you. We can accept the case. Please confirm the next steps and scheduling details."

#     return draft_text, model

# def draft_reply(
#     *,
#     subject: str | None = None,
#     sender: str | None = None,
#     body_html: str | None = None,
#     body_preview: str | None = None,
#     tone: str | None = "professional",
#     instructions: str | None = None,
# ) -> tuple[str, str]:
#     client = get_openai_client()
#     model = os.getenv("OPENAI_MODEL", "gpt-5-nano")

#     body_text = safe_text(_coerce_body_text(body_html, body_preview), 12000)

#     prompt = user_prompt_for_draft(
#         subject=safe_text(subject or "", 300),
#         sender=safe_text(sender or "", 300),
#         body_text=body_text,
#         tone=safe_text(tone or "professional", 50),
#         instructions=safe_text(instructions or "", 1000) if instructions else None,
#     )

#     resp = _responses_create_text(
#         client,
#         model=model,
#         system_text=SYSTEM_DRAFT,
#         user_text=prompt,
#         file_ids=[],
#         images=[],
#     )

#     draft_text = _response_text(resp).strip()
#     if not draft_text:
#         draft_text = "Thanks for the update. We will review and follow up with next steps."
#     return draft_text, model












































































































# app/ai/tasks.py
from __future__ import annotations

import os
import json
import base64
from typing import Optional, List, Dict

from dotenv import load_dotenv

from app.ai.client import get_openai_client
from app.ai.prompts import (
    SYSTEM_DRAFT,
    user_prompt_for_draft,
    SYSTEM_ACCEPTANCE,
    user_prompt_for_acceptance,
    SYSTEM_EMAIL_PROCESSOR,
    user_prompt_for_email_processing,
)
from app.core.sanitize import strip_html, safe_text
from app.ai.schemas import ReferralExtractOut

load_dotenv()

ALLOWED_INTENTS_DEFAULT = [
    "referral_received",
    "evaluation_received",
    "authorization_approved",
    "authorization_request",
    "staffing_confirmation",
    "non_case_email",
    "unknown",
]

ALLOWED_STATUSES_DEFAULT = [
    "new",
    "pending staffing",
    "staffed",
    "acceptance drafted",
    "acceptance sent",
    "evaluation completed",
    "authorization pending",
    "authorized – treatment started",
    "closed",
]


def _coerce_body_text(body_html: str | None, body_preview: str | None) -> str:
    body_text = body_preview or ""
    if body_html:
        body_text = strip_html(body_html) or body_text
    return safe_text(body_text, 12000)


def _response_text(resp) -> str:
    txt = getattr(resp, "output_text", None)
    if isinstance(txt, str) and txt.strip():
        return txt.strip()

    out = getattr(resp, "output", None)
    if isinstance(out, list):
        parts: List[str] = []
        for item in out:
            content = item.get("content") if isinstance(item, dict) else getattr(item, "content", None)
            if isinstance(content, list):
                for c in content:
                    t = c.get("text") if isinstance(c, dict) else getattr(c, "text", None)
                    if t:
                        parts.append(t)
        return "\n".join(parts).strip()

    return ""


# --------------------------------------------------------------------------------------
# Attachments → OpenAI (as-is) via Files API (cached by openai_file_id in DB)
# --------------------------------------------------------------------------------------

def _upload_openai_file(local_path: str) -> str:
    client = get_openai_client()
    purpose = (os.getenv("OPENAI_FILE_PURPOSE", "user_data") or "user_data").strip()
    with open(local_path, "rb") as f:
        up = client.files.create(file=f, purpose=purpose)
    return up.id


# --------------------------------------------------------------------------------------
# Vision inputs from attachments
# - PDFs (scanned) → render pages to PNG
# - Images (png/jpg/etc) → send directly as data: URL
# --------------------------------------------------------------------------------------

def _is_pdf_attachment(a: dict) -> bool:
    name = (a.get("name") or "").lower()
    ct = (a.get("content_type") or a.get("contentType") or "").lower()
    return name.endswith(".pdf") or ct in {"application/pdf", "application/x-pdf"}


def _is_image_attachment(a: dict) -> bool:
    name = (a.get("name") or "").lower()
    ct = (a.get("content_type") or a.get("contentType") or "").lower()
    if ct.startswith("image/"):
        return True
    return name.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"))


def _file_to_b64(local_path: str) -> Optional[str]:
    try:
        with open(local_path, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    except Exception:
        return None


def _pdf_pages_to_png_b64(
    local_path: str,
    *,
    dpi: int,
    max_pages: int,
) -> List[Dict]:
    """
    Render up to max_pages of a PDF to PNG images and return:
      [{"page": 1, "b64": "...", "mime": "image/png"}...]
    Uses PyMuPDF (fitz). If missing, returns [].
    """
    try:
        import fitz  # pymupdf
    except Exception:
        return []

    out: List[Dict] = []
    doc = None
    try:
        doc = fitz.open(local_path)
        zoom = float(dpi) / 72.0
        mat = fitz.Matrix(zoom, zoom)

        total = int(getattr(doc, "page_count", 0) or 0)
        n = min(total, int(max_pages))

        for i in range(n):
            page = doc.load_page(i)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            png_bytes = pix.tobytes("png")
            b64 = base64.b64encode(png_bytes).decode("ascii")
            out.append({"page": i + 1, "b64": b64, "mime": "image/png"})
    except Exception:
        return []
    finally:
        try:
            if doc is not None:
                doc.close()
        except Exception:
            pass

    return out


def _build_vision_images_from_attachments(attachments: List[dict] | None) -> List[dict]:
    """
    Returns list of:
      {"attachment_id":..., "name":..., "page":..., "mime":..., "b64":..., "kind": "pdf_page"|"image"}
    Caps are required to avoid payload blowups.
    """
    if not attachments:
        return []

    pdf_enabled = os.getenv("PDF_VISION_ENABLED", "1").strip().lower() not in {"0", "false", "no"}
    img_enabled = os.getenv("IMAGE_VISION_ENABLED", "1").strip().lower() not in {"0", "false", "no"}

    # Limits
    dpi = int(os.getenv("PDF_VISION_DPI", "180"))
    max_pages_per_pdf = int(os.getenv("PDF_VISION_MAX_PAGES", "5"))
    max_total_images = int(os.getenv("VISION_MAX_IMAGES", "10"))
    max_image_bytes = int(os.getenv("VISION_MAX_IMAGE_BYTES", "2500000"))  # 2.5MB per image guardrail

    images: List[dict] = []

    for a in attachments:
        if len(images) >= max_total_images:
            break

        local_path = (a.get("local_path") or "").strip()
        if not local_path:
            continue

        # PDF pages -> PNGs
        if pdf_enabled and _is_pdf_attachment(a):
            pages = _pdf_pages_to_png_b64(local_path, dpi=dpi, max_pages=max_pages_per_pdf)
            for p in pages:
                if len(images) >= max_total_images:
                    break
                images.append(
                    {
                        "attachment_id": a.get("attachment_id") or a.get("id"),
                        "name": a.get("name"),
                        "page": p["page"],
                        "mime": p["mime"],
                        "b64": p["b64"],
                        "kind": "pdf_page",
                    }
                )
            continue

        # Regular images (including inline images if you saved them)
        if img_enabled and _is_image_attachment(a):
            try:
                size = int(a.get("size") or 0)
                if size and size > max_image_bytes:
                    continue
            except Exception:
                pass

            b64 = _file_to_b64(local_path)
            if not b64:
                continue

            mime = (a.get("content_type") or a.get("contentType") or "").strip() or "image/png"

            images.append(
                {
                    "attachment_id": a.get("attachment_id") or a.get("id"),
                    "name": a.get("name"),
                    "page": 1,
                    "mime": mime,
                    "b64": b64,
                    "kind": "image",
                }
            )

    return images


def _responses_create_json(
    client,
    *,
    model: str,
    system_text: str,
    user_text: str,
    file_ids: List[str],
    images: List[dict] | None = None,
):
    """
    Uses Responses API.
    IMPORTANT: For images, use data: URL via image_url.
    This does NOT require any publicly accessible URL.
    """
    user_content: List[dict] = [{"type": "input_text", "text": user_text}]

    # Vision images (PDF pages + real images)
    for img in images or []:
        mime = (img.get("mime") or "image/png").strip() or "image/png"
        b64 = (img.get("b64") or "").strip()
        if not b64:
            continue
        user_content.append({"type": "input_image", "image_url": f"data:{mime};base64,{b64}"})

    # Original files as-is
    for fid in (file_ids or []):
        user_content.append({"type": "input_file", "file_id": fid})

    base = {
        "model": model,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": system_text}]},
            {"role": "user", "content": user_content},
        ],
    }

    try:
        return client.responses.create(**base, text={"format": {"type": "json_object"}})
    except TypeError:
        return client.responses.create(**base)


def _responses_create_text(
    client,
    *,
    model: str,
    system_text: str,
    user_text: str,
    file_ids: List[str] | None = None,
    images: List[dict] | None = None,
):
    user_content: List[dict] = [{"type": "input_text", "text": user_text}]

    for img in images or []:
        mime = (img.get("mime") or "image/png").strip() or "image/png"
        b64 = (img.get("b64") or "").strip()
        if not b64:
            continue
        user_content.append({"type": "input_image", "image_url": f"data:{mime};base64,{b64}"})

    for fid in (file_ids or []):
        user_content.append({"type": "input_file", "file_id": fid})

    base = {
        "model": model,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": system_text}]},
            {"role": "user", "content": user_content},
        ],
    }
    return client.responses.create(**base)


def _referral_extract_keys() -> List[str]:
    # pydantic v2: model_fields, v1: __fields__
    mf = getattr(ReferralExtractOut, "model_fields", None)
    if isinstance(mf, dict) and mf:
        return list(mf.keys())

    f1 = getattr(ReferralExtractOut, "__fields__", None)
    if isinstance(f1, dict) and f1:
        return list(f1.keys())

    return [
        "patient_name",
        "dob",
        "diagnosis",
        "address",
        "insurance",
        "discipline_requested",
        "referral_source_name",
        "referral_source_org",
        "referral_source_email",
        "referral_source_phone",
        "referral_source_fax",
        "patient_id",
        "mrn",
        "ordering_provider",
        "requested_start_date",
        "visit_frequency",
        "authorization_required",
        "language",
        "caregiver_contact",
        "special_instructions",
        "extracted_from",
        "confidence_notes",
        "evidence",
    ]


def process_email_llm(
    *,
    mailbox: str,
    subject: str | None,
    sender: str | None,
    body_html: str | None,
    body_preview: str | None,
    attachments: List[dict] | None,
    allowed_intents: List[str] | None = None,
    allowed_statuses: List[str] | None = None,
) -> tuple[dict, str]:
    """
    Unified classifier + extractor.

    Inputs:
    - Email text (subject/from/body)
    - Attachments as-is (file_ids)
    - Vision images (PDF pages + images)

    Notes:
    - Vision images are sent as data: URLs, so nothing needs to be publicly accessible.
    - This will only work for images that were actually saved as attachments (local_path present).
    """

    allowed_i = allowed_intents or ALLOWED_INTENTS_DEFAULT
    allowed_s = allowed_statuses or ALLOWED_STATUSES_DEFAULT

    body_text = safe_text(_coerce_body_text(body_html, body_preview), 12000)
    subject_s = safe_text(subject or "", 300)
    sender_s = safe_text(sender or "", 300)
    mailbox_s = safe_text(mailbox or "", 200)

    desired_extract_keys = _referral_extract_keys()

    file_ids: List[str] = []
    upload_failures: List[str] = []

    try:
        from app.mysql_ops import MysqlOps
        ops = MysqlOps()
    except Exception:
        ops = None

    # Build vision images from saved attachments (PDF pages + images)
    vision_images = _build_vision_images_from_attachments(attachments or [])

    # Upload attachments as-is (cached via openai_file_id)
    for a in attachments or []:
        try:
            local_path = (a.get("local_path") or "").strip()
            if not local_path:
                continue

            cached = (a.get("openai_file_id") or "").strip()
            if cached:
                file_ids.append(cached)
                continue

            fid = _upload_openai_file(local_path)
            file_ids.append(fid)

            if ops and a.get("id"):
                try:
                    ops.set_attachment_openai_file_id(int(a["id"]), fid)
                except Exception:
                    pass

        except Exception as e:
            upload_failures.append(f"id={a.get('id')} err={type(e).__name__}")

    client = get_openai_client()
    model = os.getenv("OPENAI_MODEL", "gpt-5-nano")

    prompt = user_prompt_for_email_processing(
        mailbox=mailbox_s,
        subject=subject_s,
        sender=sender_s,
        body_text=body_text,
        allowed_intents=allowed_i,
        allowed_statuses=allowed_s,
    )

    prompt += f"""

Extraction requirements (IMPORTANT):
- Many attachments are scanned PDFs and/or screenshots. Use the attached images (rendered PDF pages + image attachments) to extract patient/referral details.
- Populate extracted with as many of these keys as you can find (use null if missing):
{desired_extract_keys}

Evidence requirement:
- If you extract patient_name/dob/diagnosis/insurance/mrn/address, include short evidence snippets inside extracted.evidence when possible.
- If the evidence comes from a PDF page image, include the page number in the evidence string when you can (e.g., "Page 2: DOB 01/02/1980").
"""

    resp = _responses_create_json(
        client,
        model=model,
        system_text=SYSTEM_EMAIL_PROCESSOR,
        user_text=prompt,
        file_ids=file_ids,
        images=vision_images,
    )

    raw = _response_text(resp)

    try:
        out = json.loads(raw)
    except Exception:
        out = {
            "intent": "unknown",
            "confidence": 0.0,
            "signals": ["json_parse_failed"],
            "extracted": None,
            "recommended_status": None,
        }

    # Signals (debug)
    if file_ids:
        out["signals"] = (out.get("signals") or []) + ["files_attached"]
    if vision_images:
        out["signals"] = (out.get("signals") or []) + [f"vision_images:{len(vision_images)}"]
    if upload_failures:
        out["signals"] = (out.get("signals") or []) + ["attachment_upload_failed"]
        out["attachment_upload_failures"] = upload_failures[:5]

    # Enforce allowed intent/status
    if out.get("intent") not in allowed_i:
        out["intent"] = "unknown"
        out["confidence"] = 0.0
        out["signals"] = (out.get("signals") or []) + ["intent_not_allowed"]

    if out.get("recommended_status") not in allowed_s:
        out["recommended_status"] = None

    out.setdefault("confidence", 0.0)
    out.setdefault("signals", [])
    out.setdefault("extracted", None)
    out.setdefault("recommended_status", None)

    return out, model


# --------------------------------------------------------------------------------------
# Drafting helpers
# --------------------------------------------------------------------------------------

def draft_case_acceptance(
    *,
    case_title: str,
    referral_source_email: str | None,
    therapist_name: str | None,
    discipline: str | None,
    availability: str | None,
) -> tuple[str, str]:
    client = get_openai_client()
    model = os.getenv("OPENAI_MODEL", "gpt-5-nano")

    prompt = user_prompt_for_acceptance(
        case_title=safe_text(case_title or "", 400),
        referral_source_email=safe_text(referral_source_email or "", 300),
        therapist_name=safe_text(therapist_name or "", 200),
        discipline=safe_text(discipline or "", 200),
        availability=safe_text(availability or "", 400),
    )

    resp = _responses_create_text(
        client,
        model=model,
        system_text=SYSTEM_ACCEPTANCE,
        user_text=prompt,
        file_ids=[],
        images=[],
    )

    draft_text = _response_text(resp).strip()
    if not draft_text:
        draft_text = "Thank you. We can accept the case. Please confirm the next steps and scheduling details."

    return draft_text, model


def draft_reply(
    *,
    subject: str | None = None,
    sender: str | None = None,
    body_html: str | None = None,
    body_preview: str | None = None,
    tone: str | None = "professional",
    instructions: str | None = None,
) -> tuple[str, str]:
    client = get_openai_client()
    model = os.getenv("OPENAI_MODEL", "gpt-5-nano")

    body_text = safe_text(_coerce_body_text(body_html, body_preview), 12000)

    prompt = user_prompt_for_draft(
        subject=safe_text(subject or "", 300),
        sender=safe_text(sender or "", 300),
        body_text=body_text,
        tone=safe_text(tone or "professional", 50),
        instructions=safe_text(instructions or "", 1000) if instructions else None,
    )

    resp = _responses_create_text(
        client,
        model=model,
        system_text=SYSTEM_DRAFT,
        user_text=prompt,
        file_ids=[],
        images=[],
    )

    draft_text = _response_text(resp).strip()
    if not draft_text:
        draft_text = "Thanks for the update. We will review and follow up with next steps."
    return draft_text, model
