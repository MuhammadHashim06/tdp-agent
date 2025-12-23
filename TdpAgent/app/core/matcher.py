from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import re

@dataclass
class MatchResult:
    case_key: Optional[str] = None
    reason: str = "no_match"

_CASE_ID_RE = re.compile(r"\bCASE[- ]?(\d{3,})\b", re.IGNORECASE)

def match_case_from_subject(subject: str) -> MatchResult:
    if not subject:
        return MatchResult()
    m = _CASE_ID_RE.search(subject)
    if not m:
        return MatchResult()
    return MatchResult(case_key=f"CASE-{m.group(1)}", reason="case_id_in_subject")
