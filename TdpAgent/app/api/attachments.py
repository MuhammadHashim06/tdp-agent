from __future__ import annotations

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.mysql_ops import MysqlOps

router = APIRouter()

def _safe_abs_path(p: str) -> str:
    if not p:
        raise HTTPException(status_code=404, detail="Attachment file missing")

    abs_p = os.path.abspath(p)
    base = os.path.abspath(os.path.join(os.getcwd(), "storage", "attachments"))

    # Prevent path traversal / arbitrary file download
    if not abs_p.startswith(base + os.sep) and abs_p != base:
        raise HTTPException(status_code=400, detail="Invalid attachment path")

    if not os.path.exists(abs_p):
        raise HTTPException(status_code=404, detail="Attachment file not found")

    return abs_p


@router.get("/emails/{email_id}")
def list_attachments(email_id: int):
    ops = MysqlOps()
    email = ops.get_email_by_id(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    rows = ops.list_attachments_for_email(email_id)
    return {
        "email_id": email_id,
        "count": len(rows),
        "items": [
            {
                "id": a.id,
                "attachment_id": a.attachment_id,
                "name": a.name,
                "content_type": a.content_type,
                "size": a.size,
                "is_inline": bool(a.is_inline),
                "content_id": a.content_id,
                "local_path": a.local_path,
                "openai_file_id": getattr(a, "openai_file_id", None),
            }
            for a in rows
        ],
    }


@router.get("/{attachment_row_id}/download")
def download_attachment(attachment_row_id: int):
    ops = MysqlOps()
    # You don't have a direct getter; easiest is query by email list,
    # but better to add a small method. For now, do a quick workaround:
    # Add this method in MysqlOps if you want it clean.
    from sqlalchemy import select
    from app.db import SessionLocal
    from app.models import EmailAttachment

    with SessionLocal() as db:
        a = db.get(EmailAttachment, attachment_row_id)

    if not a:
        raise HTTPException(status_code=404, detail="Attachment not found")

    abs_path = _safe_abs_path(a.local_path or "")
    filename = a.name or os.path.basename(abs_path)

    return FileResponse(
        abs_path,
        media_type=a.content_type or "application/octet-stream",
        filename=filename,
    )
