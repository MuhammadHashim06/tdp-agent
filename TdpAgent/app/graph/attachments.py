# from __future__ import annotations

# import requests
# from typing import Any, Dict, List

# from app.graph.auth import get_graph_token

# GRAPH_BASE = "https://graph.microsoft.com/v1.0"


# def _headers() -> Dict[str, str]:
#     return {
#         "Authorization": f"Bearer {get_graph_token()}",
#         "Accept": "application/json",
#     }


# def fetch_attachments(mailbox: str, message_id: str) -> List[Dict[str, Any]]:
#     url = f"{GRAPH_BASE}/users/{mailbox}/messages/{message_id}/attachments"
#     r = requests.get(url, headers=_headers(), timeout=60)
#     r.raise_for_status()
#     return (r.json().get("value", []) or [])



# app/graph/attachments.py
from __future__ import annotations

import requests
from typing import Any, Dict, List, Optional

from app.graph.auth import get_graph_token

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def _headers(accept_json: bool = True) -> Dict[str, str]:
    h = {"Authorization": f"Bearer {get_graph_token()}"}
    if accept_json:
        h["Accept"] = "application/json"
    return h


def _get(url: str, params: Optional[dict] = None) -> dict:
    r = requests.get(url, headers=_headers(accept_json=True), params=params, timeout=60)
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise requests.HTTPError(f"{e} detail={detail}") from e
    return r.json() if r.content else {}


def fetch_attachment_bytes(mailbox: str, message_id: str, attachment_id: str) -> bytes:
    """
    Download raw attachment bytes using /$value.
    This works even when contentBytes is omitted for fileAttachment.
    """
    if not mailbox or not message_id or not attachment_id:
        return b""

    url = f"{GRAPH_BASE}/users/{mailbox}/messages/{message_id}/attachments/{attachment_id}/$value"
    r = requests.get(url, headers=_headers(accept_json=False), timeout=120)
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        # Try to surface Graph JSON error if it exists; otherwise raw text
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise requests.HTTPError(f"{e} detail={detail}") from e
    return r.content or b""


def fetch_attachments(mailbox: str, message_id: str) -> List[Dict[str, Any]]:
    """
    Graph attachments list often omits contentBytes.
    We return attachment metadata only; if caller needs bytes, use fetch_attachment_bytes().

    Notes:
    - Do NOT include @odata.type or contentId in $select on the collection; Graph rejects these.
    - The returned payload usually includes @odata.type even when not selected.
    """
    base = f"{GRAPH_BASE}/users/{mailbox}/messages/{message_id}/attachments"

    # 1) list metadata (Graph rejects @odata.type in $select)
    data = _get(
        base,
        params={"$select": "id,name,contentType,size,isInline"},
    )

    items = (data.get("value", []) or [])
    if not items:
        return []

    # Keep it simple: return items as-is (metadata only)
    return items
