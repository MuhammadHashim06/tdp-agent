from __future__ import annotations

INTENT_TO_STATUS = {
    "referral_received": "pending staffing",
    "staffing_confirmation": "staffed",
    "evaluation_received": "evaluation completed",
    "authorization_request": "authorization pending",
    "authorization_approved": "authorized – treatment started",
}

TERMINAL_STATUSES = {"closed"}

def can_apply_intent(current_status: str | None, intent: str) -> bool:
    s = (current_status or "").strip().lower()
    if s in TERMINAL_STATUSES:
        return False
    # Add stricter rules later if needed
    return intent in INTENT_TO_STATUS

def status_for_intent(intent: str) -> str | None:
    return INTENT_TO_STATUS.get(intent)
