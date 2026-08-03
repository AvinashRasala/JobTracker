import uuid
from datetime import datetime

from pydantic import BaseModel


class GmailStatus(BaseModel):
    connected: bool
    last_synced_at: datetime | None


class GmailSyncResult(BaseModel):
    new_applications: int
    status_updates: int
    ignored: int
    errors: list[str]


class GmailAuthUrl(BaseModel):
    auth_url: str


class GmailStatusChange(BaseModel):
    status_history_id: uuid.UUID
    application_id: uuid.UUID
    role_title: str
    company_name: str | None
    from_status: str | None
    to_status: str
    note: str | None
    created_at: datetime


class GmailSkippedEmail(BaseModel):
    gmail_message_id: str
    subject: str | None
    sender: str | None
    created_at: datetime
