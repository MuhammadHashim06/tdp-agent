from __future__ import annotations

import os
import re
import hashlib
from typing import Optional


def _safe_filename(name: str) -> str:
    name = (name or "attachment.bin").strip().replace("\x00", "")
    name = re.sub(r"[<>:\"/\\|?*\n\r\t]", "_", name)  # invalid chars on Windows
    name = re.sub(r"\s+", " ", name).strip()
    return name or "attachment.bin"


def save_file_attachment(
    mailbox: str,            # kept for interface consistency; not used in path
    email_id: int,
    attachment: dict,
    content_bytes: bytes,
) -> Optional[str]:
    attachment_id = (attachment.get("id") or "").strip()
    filename = _safe_filename(attachment.get("name") or "attachment.bin")

    # Keep filename short to avoid Windows MAX_PATH issues
    if len(filename) > 120:
        root, ext = os.path.splitext(filename)
        filename = root[:110] + ext[:10]

    # Short ID to keep path short and stable
    short_id = hashlib.md5(attachment_id.encode("utf-8")).hexdigest()[:16] if attachment_id else "unknown"

    # Per-email folder
    base_dir = os.path.join(os.getcwd(), "storage", "attachments", str(email_id))
    os.makedirs(base_dir, exist_ok=True)

    # Optional: add a small content hash to avoid overwriting if same short_id repeats
    content_sig = hashlib.md5(content_bytes).hexdigest()[:8] if content_bytes else "empty"

    path = os.path.join(base_dir, f"{short_id}_{content_sig}_{filename}")

    with open(path, "wb") as f:
        f.write(content_bytes)

    return path
