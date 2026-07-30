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
