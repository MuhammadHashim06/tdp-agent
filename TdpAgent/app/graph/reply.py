from __future__ import annotations

import requests
from typing import Dict, Any, Optional, List

from app.graph.auth import get_graph_token

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {get_graph_token()}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def create_reply_draft(mailbox: str, message_id: str) -> Dict[str, Any]:
    """
    Creates a reply draft for an existing message.
    POST /users/{mailbox}/messages/{message_id}/createReply
    Returns the draft Message object (includes draft id).
    """
    url = f"{GRAPH_BASE}/users/{mailbox}/messages/{message_id}/createReply"
    r = requests.post(url, headers=_headers(), json={}, timeout=60)
    r.raise_for_status()
    return r.json()


def update_draft_message(
    mailbox: str,
    draft_message_id: str,
    *,
    body_html: str,
    to_recipients: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    PATCH the draft message content (and optionally recipients).
    """
    url = f"{GRAPH_BASE}/users/{mailbox}/messages/{draft_message_id}"

    payload: Dict[str, Any] = {
        "body": {
            "contentType": "HTML",
            "content": body_html,
        }
    }

    if to_recipients:
        payload["toRecipients"] = [
            {"emailAddress": {"address": addr}} for addr in to_recipients if addr
        ]

    r = requests.patch(url, headers=_headers(), json=payload, timeout=60)
    r.raise_for_status()
    return r.json()

def send_draft_message(mailbox: str, draft_message_id: str) -> None:
    """
    Sends an existing draft message.
    POST /users/{mailbox}/messages/{draft_message_id}/send
    Returns 202 Accepted with empty body.
    """
    url = f"{GRAPH_BASE}/users/{mailbox}/messages/{draft_message_id}/send"
    r = requests.post(url, headers=_headers(), json={}, timeout=60)
    r.raise_for_status()
