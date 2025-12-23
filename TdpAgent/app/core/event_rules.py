# app/core/event_rules.py

from __future__ import annotations
from typing import Optional, Dict, Any
import re

_EVAL_RE = re.compile(r"\b(?:ot|pt|st)?\s*eval(?:uation)?\b", re.IGNORECASE)
_AUTH_RE = re.compile(r"\b(?:prior\s*auth|prior\s*authorization|authorization)\b", re.IGNORECASE)

# Auth request / pending (non-approved, non-denied)
_AUTH_REQUEST_RE = re.compile(
    r"\b(?:"
    r"auth(?:orization)?\s*(?:needed|required|requested|request(?:ed)?)|"
    r"request\s*for\s*(?:auth|authorization)|"
    r"(?:auth|authorization)\s*(?:pending|needed|required)|"
    r"pending\s*(?:auth|authorization)|"
    r"need\s*(?:prior\s*)?auth|"
    r"prior\s*auth\s*(?:needed|required)"
    r")\b",
    re.IGNORECASE,
)

def classify_email_event(
    email: Dict[str, Any],
    mailbox: str,
    attachments: list[dict] | None = None,
) -> Optional[str]:
    sender = (email.get("sender") or "").lower()
    subject = (email.get("subject") or "")
    subject_l = subject.lower()
    body_preview_l = (email.get("body_preview") or "").lower()

    mb = (mailbox or "").lower()

    # Treat these mailboxes as "intake-ish"
    is_staffing_like = mb.startswith("staffing@")
    is_services_like = mb.startswith("services@") or mb.startswith("schedulingtdp@")

    internal_domain = "@therapydepotonline.com"
    is_external = internal_domain not in sender

    # Stage 1: Referral intake (typically external -> staffing)
    if is_staffing_like:
        referral_keywords = [
            "new case referral",
            "securemail: new case referral",
            "referral",
            "facesheet",
            "face sheet",
            "demographics",
            "patient referral",
        ]
        has_referral_signal = any(k in subject_l or k in body_preview_l for k in referral_keywords)
        if is_external and has_referral_signal:
            return "referral_received"

    if is_services_like:
        # Stage 4: Evaluation received
        if _EVAL_RE.search(subject) or _EVAL_RE.search(body_preview_l):
            return "evaluation_received"

        # Attachment name heuristic
        if attachments:
            for a in attachments:
                name = (a.get("name") or "")
                if name and _EVAL_RE.search(name):
                    return "evaluation_received"

        # Stage 5: Authorization request / pending
        if _AUTH_REQUEST_RE.search(subject) or _AUTH_REQUEST_RE.search(body_preview_l):
            return "authorization_request"

        # Backup: generic auth mention WITHOUT approval/denial language => treat as request/pending
        if _AUTH_RE.search(subject) or _AUTH_RE.search(body_preview_l):
            approval_words = ["approved", "approval", "authorized", "granted"]
            denial_words = ["denied", "rejected", "not approved"]
            if not any(w in subject_l or w in body_preview_l for w in approval_words + denial_words):
                return "authorization_request"

        # Stage 6: Authorization approval received
        auth_approved_keywords = [
            "authorization approved",
            "auth approved",
            "approved authorization",
            "prior auth approved",
            "pa approved",
            "approved pa",
        ]
        if any(k in subject_l or k in body_preview_l for k in auth_approved_keywords):
            return "authorization_approved"

        # Backup: detect generic auth text + approval word
        if (_AUTH_RE.search(subject) or _AUTH_RE.search(body_preview_l)) and (
            "approved" in subject_l or "approved" in body_preview_l
        ):
            return "authorization_approved"

    return None
