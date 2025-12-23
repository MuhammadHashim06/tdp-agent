from __future__ import annotations

import requests
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.graph.auth import get_graph_token
from app.core.sanitize import safe_email

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {get_graph_token()}",
        "Accept": "application/json",
    }


# Keep the selected fields consistent across delta + since
_SELECT_FIELDS = (
    "id,"
    "internetMessageId,"
    "subject,"
    "receivedDateTime,"
    "conversationId,"
    "bodyPreview,"
    "from,"
    "toRecipients,"
    "ccRecipients,"
    "body,"
    "hasAttachments"
)


def fetch_messages_delta_for_mailbox(
    mailbox: str,
    delta_link: Optional[str],
    top: int,
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    If delta_link exists: fetch up to `top` changes and return quickly (ok to stop early).
    If delta_link missing (baseline): MUST paginate until @odata.deltaLink is returned,
    otherwise you never "lock in" delta state.

    Returns (messages, new_delta_link_or_none)
    """
    if delta_link:
        url = delta_link
    else:
        url = (
            f"{GRAPH_BASE}/users/{mailbox}/mailFolders/Inbox/messages/delta"
            f"?$top={top}&$select={_SELECT_FIELDS}"
        )

    items: List[Dict[str, Any]] = []
    next_delta: Optional[str] = None

    # baseline needs full walk to reach @odata.deltaLink
    baseline = delta_link is None

    while url:
        r = requests.get(url, headers=_headers(), timeout=60)
        r.raise_for_status()
        j = r.json()

        items.extend(j.get("value", []) or [])

        # deltaLink appears only at the end of paging
        if j.get("@odata.deltaLink"):
            next_delta = j["@odata.deltaLink"]
            break

        # keep going if there's a nextLink
        url = j.get("@odata.nextLink")

        # if NOT baseline, we can return quickly after collecting `top` items
        if (not baseline) and len(items) >= top:
            break

        # baseline safety: if Graph doesn't give nextLink and no deltaLink, we can't continue
        if baseline and not url:
            break

    # We only return up to `top` messages to limit processing load,
    # but baseline still paged until deltaLink.
    # If baseline, return everything we collected (do NOT truncate),
    # because truncating + storing deltaLink skips history forever.
    if baseline:
        return items, next_delta

    return items[:top], next_delta


def fetch_messages_since_iso_for_mailbox(mailbox: str, since_iso: str, top: int) -> List[Dict[str, Any]]:
    url = f"{GRAPH_BASE}/users/{mailbox}/mailFolders/Inbox/messages"
    params = {
        "$top": str(top),
        "$orderby": "receivedDateTime desc",
        "$filter": f"receivedDateTime ge {since_iso}",
        "$select": _SELECT_FIELDS,
    }
    r = requests.get(url, headers=_headers(), params=params, timeout=60)
    r.raise_for_status()
    return (r.json().get("value", []) or [])


def to_email_item(raw: Dict[str, Any], mailbox: str) -> Dict[str, Any]:
    fr = raw.get("from", {}).get("emailAddress", {}) or {}
    sender = safe_email(fr.get("address", "") or "")
    sender_name = fr.get("name", "") or ""

    to_list: List[str] = []
    for x in raw.get("toRecipients", []) or []:
        addr = (x.get("emailAddress", {}) or {}).get("address", "")
        if addr:
            to_list.append(safe_email(addr))

    cc_list: List[str] = []
    for x in raw.get("ccRecipients", []) or []:
        addr = (x.get("emailAddress", {}) or {}).get("address", "")
        if addr:
            cc_list.append(safe_email(addr))

    body = raw.get("body") or {}
    content = body.get("content")
    content_type = body.get("contentType")
    body_html = content if content_type == "html" else None

    return {
        "message_id": raw.get("id"),
        "internet_message_id": raw.get("internetMessageId"),
        "subject": raw.get("subject"),
        "sender": sender,
        "sender_name": sender_name,
        "to": to_list,
        "cc": cc_list,
        "received_datetime": raw.get("receivedDateTime"),
        "body_preview": raw.get("bodyPreview"),
        "body_html": body_html,
        "conversation_id": raw.get("conversationId"),
        "has_attachments": bool(raw.get("hasAttachments", False)),
        "mailbox": mailbox,  # store which mailbox this was fetched from (useful later)
        "raw": raw,  # mysql_ops serializes to string
    }


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def prime_delta_cursor_for_mailbox(mailbox: str, top: int = 50) -> str:
    """
    Walk the delta feed until Graph returns @odata.deltaLink.
    We do NOT return/process baseline items. This is purely to get a stable cursor.
    """
    url = (
        f"{GRAPH_BASE}/users/{mailbox}/mailFolders/Inbox/messages/delta"
        f"?$top={top}&$select=id"
    )

    while url:
        r = requests.get(url, headers=_headers(), timeout=60)
        r.raise_for_status()
        j = r.json()

        dl = j.get("@odata.deltaLink")
        if dl:
            return dl

        url = j.get("@odata.nextLink")

    raise RuntimeError("Delta prime did not return @odata.deltaLink")
