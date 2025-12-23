from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class Settings(BaseModel):
    # App
    APP_ENV: str = Field(default="local")
    APP_NAME: str = Field(default="TdpAgent")
    LOG_LEVEL: str = Field(default="INFO")

    # OpenAI
    OPENAI_API_KEY: str = Field(default="")
    OPENAI_MODEL: str = Field(default="gpt-5-nano")

    # Microsoft Graph (client credentials)
    MS_TENANT_ID: str = Field(default="")
    MS_CLIENT_ID: str = Field(default="")
    MS_CLIENT_SECRET: str = Field(default="")
    MS_USER_ID: str = Field(default="")  # user mailbox UPN or id
    GRAPH_SCOPE: str = Field(default="https://graph.microsoft.com/.default")
    GRAPH_FETCH_LIMIT: int = Field(default=10)

    # Tadabase
    TADABASE_BASE_URL: str = Field(default="https://api.tadabase.io/api/v1")
    TADABASE_APP_ID: str = Field(default="")
    TADABASE_API_KEY: str = Field(default="")
    # Data table ids
    TADABASE_TABLE_EMAILS: str = Field(default="")
    TADABASE_TABLE_CASES: str = Field(default="")
    TADABASE_TABLE_DRAFTS: str = Field(default="")
    TADABASE_TABLE_SYNC_STATE: str = Field(default="")  # store deltaLink/lastSync

    # Worker
    POLL_INTERVAL_SECONDS: int = Field(default=30)


class EmailItem(BaseModel):
    message_id: str
    internet_message_id: Optional[str] = None
    subject: Optional[str] = None
    sender: Optional[str] = None
    sender_name: Optional[str] = None
    to: List[str] = Field(default_factory=list)
    cc: List[str] = Field(default_factory=list)
    received_datetime: Optional[str] = None
    body_preview: Optional[str] = None
    body_html: Optional[str] = None
    conversation_id: Optional[str] = None
    raw: Dict[str, Any] = Field(default_factory=dict)


class DraftRequest(BaseModel):
    email_id: str
    tone: str = "professional"
    instructions: Optional[str] = None


class DraftResponse(BaseModel):
    draft: str
    model: str


class CaseCreate(BaseModel):
    external_id: Optional[str] = None
    title: str
    status: str = "new"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
