# app/ai/prompts.py

SYSTEM_DRAFT = """You are an assistant that drafts concise, compliant, professional email replies.
Rules:
- Use plain English.
- Do not invent facts.
- If missing info, ask 1-3 clear questions.
- Keep it brief unless the user requests detail.
"""

def user_prompt_for_draft(subject: str, sender: str, body_text: str, tone: str, instructions: str | None) -> str:
    extra = f"\nExtra instructions: {instructions}" if instructions else ""
    return f"""Draft a reply.

Subject: {subject}
From: {sender}
Tone: {tone}

Email body:
{body_text}
{extra}
"""


SYSTEM_ACCEPTANCE = """You draft concise, compliant, professional case acceptance emails.

Hard rules:
- Do not invent facts. Do not use placeholders like [Your Name], [Phone], etc.
- If therapist_name is missing, do NOT claim a therapist is assigned.
- If referral_source_email is missing, ask for the best contact email.
- Keep it short and operational.
"""

def user_prompt_for_acceptance(
    case_title: str,
    referral_source_email: str | None,
    therapist_name: str | None,
    discipline: str | None,
    availability: str | None,
) -> str:
    return f"""Draft a case acceptance email to the referral source.

Case title/patient identifier: {case_title}

Known details:
- Referral source email: {referral_source_email or "MISSING"}
- Therapist name: {therapist_name or "MISSING"}
- Discipline: {discipline or "MISSING"}
- Availability: {availability or "MISSING"}

Requirements:
- Confirm the case has been accepted.
- Evaluation: say the initial evaluation is pending and will be scheduled.
- Therapist assignment:
  - If therapist_name is provided: state the assigned therapist name (and discipline if provided).
  - If therapist_name is NOT provided: say staffing is in progress.
- If referral source email is MISSING: ask for the best contact email.
- Do not mention internal systems.
- Do not include any signature placeholders.
"""


# --------------------------------------------------------------------------------------
# NEW: Unified email processing (classification + extraction) with attachments "as-is"
# --------------------------------------------------------------------------------------

SYSTEM_EMAIL_PROCESSOR = """You process inbound operational healthcare emails for case coordination.

Hard rules:
- Output MUST be valid JSON only. No commentary.
- Choose intent ONLY from allowed_intents.
- Do not invent facts. If a value is missing, return null.
- Do not infer clinical facts beyond what's explicitly stated.
- If ambiguous, set intent to "unknown" with low confidence.
- Use mailbox + subject + body + attachments to decide.
"""

def user_prompt_for_email_processing(
    mailbox: str,
    subject: str,
    sender: str,
    body_text: str,
    allowed_intents: list[str],
    allowed_statuses: list[str],
) -> str:
    return f"""Process this email.

Allowed intents:
{allowed_intents}

Allowed statuses:
{allowed_statuses}

Mailbox: {mailbox}
From: {sender}
Subject: {subject}

Body:
{body_text}

Return JSON with exactly:
- intent: one of allowed_intents
- confidence: number from 0 to 1
- signals: array of short strings (0-5 items)
- extracted: object (keys/values you found) OR null
- recommended_status: one of allowed_statuses OR null
"""


# --------------------------------------------------------------------------------------
# Legacy prompts kept for backward compatibility (older flow)
# --------------------------------------------------------------------------------------

SYSTEM_REFERRAL_EXTRACT = """You extract structured referral data from an email + extracted attachment text.

Hard rules:
- Do not invent facts. If missing, return null.
- Prefer exact values as written.
- Do not guess patient details.
- If multiple patients/cases exist, return the primary one (or the first clearly identified).
- Output must be valid JSON and follow the schema strictly.
"""

def user_prompt_for_referral_extract(
    subject: str,
    sender: str,
    body_text: str,
    attachments: list[dict] | None,
    attachments_text: str | None,
) -> str:
    att_lines = []
    for a in attachments or []:
        name = (a.get("name") or "").strip()
        ct = (a.get("content_type") or "").strip()
        size = a.get("size")
        lp = (a.get("local_path") or "").strip()
        if name or ct or lp:
            att_lines.append(f"- {name} | {ct} | {size} | {lp}")

    att_block = "\n".join(att_lines) if att_lines else "(none)"
    att_text_block = (attachments_text or "").strip() or "(none)"

    return f"""Extract referral details from this email.

Subject: {subject}
From: {sender}

Email body (cleaned):
{body_text}

Attachments (metadata):
{att_block}

Attachments text (extracted locally; may be partial):
{att_text_block}

Return fields as JSON (no commentary)."""


SYSTEM_INTENT_CLASSIFIER = """You classify a single inbound email into one of the allowed intents.

Hard rules:
- Choose ONLY from allowed_intents.
- Do not invent new labels.
- Do not infer clinical facts.
- Use mailbox + subject + body + attachment metadata/text to decide.
- If ambiguous, return "unknown".
- Output MUST be valid JSON only (no commentary).
"""

def user_prompt_for_intent_classification(
    mailbox: str,
    subject: str | None,
    sender: str | None,
    body_text: str,
    allowed_intents: list[str],
    attachments: list[dict] | None,
    attachments_text: str | None,
) -> str:
    att_lines = []
    for a in attachments or []:
        name = (a.get("name") or "").strip()
        ct = (a.get("content_type") or a.get("contentType") or "").strip()
        size = a.get("size")
        lp = (a.get("local_path") or "").strip()
        if name or ct or lp:
            att_lines.append(f"- {name} | {ct} | {size} | {lp}")
    att_block = "\n".join(att_lines) if att_lines else "(none)"
    att_text_block = (attachments_text or "").strip() or "(none)"

    return f"""Classify this email into one intent.

Allowed intents:
{allowed_intents}

Mailbox: {mailbox}
From: {sender or ""}
Subject: {subject or ""}

Body (cleaned):
{body_text}

Attachments (metadata):
{att_block}

Attachments text (extracted locally; may be partial):
{att_text_block}

Return JSON with exactly:
- intent: one of allowed_intents
- confidence: number from 0 to 1
- signals: array of short strings (0-5 items) explaining why
"""
