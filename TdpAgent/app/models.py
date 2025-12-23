from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, UniqueConstraint
from sqlalchemy.sql import func
from app.db import Base
from sqlalchemy.dialects.mysql import LONGTEXT, BINARY
from sqlalchemy.ext.mutable import MutableDict
from datetime import datetime

def utcnow():
    # naive UTC (what MySQL DATETIME expects)
    return datetime.utcnow()

class Email(Base):
    __tablename__ = "emails"
    id = Column(Integer, primary_key=True)
    mailbox = Column(String(255), nullable=True)
    case_id = Column(Integer, nullable=True)

    message_id = Column(String(1024), nullable=False)  # no longer unique
    message_id_hash = Column(BINARY(16), nullable=False)
    __table_args__ = (
        UniqueConstraint("mailbox", "message_id_hash", name="uq_emails_mailbox_msg_hash"),
    )

    internet_message_id = Column(String(512))
    subject = Column(String(500))
    sender = Column(String(255))
    sender_name = Column(String(255))

    to_list = Column(LONGTEXT)
    cc_list = Column(LONGTEXT)

    received_datetime = Column(String(64))

    body_preview = Column(LONGTEXT)
    body_html = Column(LONGTEXT)

    conversation_id = Column(String(255))
    raw_json = Column(LONGTEXT, nullable=True)  # safest; JSON can hit size limits fast
    received_at = Column(DateTime, nullable=True)

    openai_file_id = Column(String(255), nullable=True)
    openai_uploaded_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now())


class SyncState(Base):
    __tablename__ = "sync_state"
    id = Column(Integer, primary_key=True)
    mailbox = Column(String(255), nullable=False, unique=True)
    delta_link = Column(LONGTEXT)
    last_sync_iso = Column(String(64))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True)
    external_id = Column(String(512), unique=True)
    title = Column(String(500), nullable=False)
    status = Column(String(50), nullable=False, default="new")
    metadata_json = Column(MutableDict.as_mutable(JSON), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

class Draft(Base):
    __tablename__ = "drafts"
    id = Column(Integer, primary_key=True)
    email_id = Column(Integer, nullable=False)

    # NEW: type + approval
    kind = Column(String(64), nullable=True)                 # e.g. acceptance, followup, internal_notify
    requires_approval = Column(Integer, nullable=False, default=1)  # 1/0 for MySQL friendliness
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String(255), nullable=True)

    draft = Column(LONGTEXT, nullable=False)
    model = Column(String(100), nullable=False)
    tone = Column(String(50))
    status = Column(String(32), nullable=False, default="draft")
    mailbox = Column(String(255), nullable=True)
    sent_message_id = Column(String(1024), nullable=True)
    sent_at = Column(DateTime, nullable=True)

    graph_draft_message_id = Column(String(1024), nullable=True)
    graph_draft_web_link = Column(String(1024), nullable=True)

    created_at = Column(DateTime, server_default=func.now())

class EmailAttachment(Base):
    __tablename__ = "email_attachments"

    id = Column(Integer, primary_key=True)
    email_id = Column(Integer, nullable=False)

    attachment_id = Column(String(255), nullable=False)  # Graph attachment id
    name = Column(String(512))
    content_type = Column(String(255))
    size = Column(Integer)

    is_inline = Column(Integer, default=0)
    content_id = Column(String(255), nullable=True)

    local_path = Column(String(1024), nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    openai_file_id = Column(String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint("email_id", "attachment_id", name="uq_email_attachment"),
    )

class CaseEvent(Base):
    __tablename__ = "case_events"

    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, nullable=False)
    email_id = Column(Integer, nullable=True)

    event_type = Column(String(64), nullable=False)     # e.g. referral_received
    actor = Column(String(16), nullable=False, default="ai")  # ai|human

    payload_json = Column(MutableDict.as_mutable(JSON), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("case_id", "email_id", "event_type", name="uq_case_event_once"),
    )
