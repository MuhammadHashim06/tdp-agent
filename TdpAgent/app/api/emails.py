from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from app.mysql_ops import MysqlOps

router = APIRouter()

@router.get("/")
def list_emails(limit: int = Query(default=50, ge=1, le=200)):
    ops = MysqlOps()
    rows = ops.list_emails(limit=limit)
    return {
        "items": [
            {
                "id": r.id,
                "subject": r.subject,
                "sender": r.sender,
                "sender_name": r.sender_name,
                "received_datetime": r.received_datetime,
                "message_id": r.message_id,
                "internet_message_id": r.internet_message_id,
                "conversation_id": r.conversation_id,
            }
            for r in rows
        ]
    }

@router.get("/{email_id}")
def get_email(email_id: int):
    ops = MysqlOps()
    r = ops.get_email_by_id(email_id)
    if not r:
        raise HTTPException(status_code=404, detail="Email not found")

    return {
        "id": r.id,
        "subject": r.subject,
        "sender": r.sender,
        "sender_name": r.sender_name,
        "to_list": r.to_list,
        "cc_list": r.cc_list,
        "received_datetime": r.received_datetime,
        "body_preview": r.body_preview,
        "body_html": r.body_html,
        "message_id": r.message_id,
        "internet_message_id": r.internet_message_id,
        "conversation_id": r.conversation_id,
        "raw_json": r.raw_json,
    }
