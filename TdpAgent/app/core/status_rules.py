def normalize_status(status: str) -> str:
    if not status:
        return "new"

    s = status.strip().lower()

    allowed = {
        "new",
        "pending staffing",
        "staffed",
        "acceptance drafted",
        "acceptance sent",
        "evaluation completed",
        "authorization pending",
        "authorized – treatment started",
        "authorized - treatment started",  # allow hyphen variant
        "closed",
    }

    if s == "authorized - treatment started":
        s = "authorized – treatment started"

    return s if s in allowed else "new"