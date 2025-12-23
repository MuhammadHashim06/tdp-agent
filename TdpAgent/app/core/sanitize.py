import re
from html import unescape

_TAG_RE = re.compile(r"<[^>]+>")

def strip_html(html: str) -> str:
    if not html:
        return ""
    text = _TAG_RE.sub(" ", html)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def safe_email(s: str) -> str:
    if not s:
        return ""
    return s.strip().lower()

def safe_text(s: str, max_len: int = 5000) -> str:
    if not s:
        return ""
    s = s.strip()
    if len(s) > max_len:
        s = s[:max_len]
    return s
