import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProcessedGmailMessage(Base):
    """
    Tracks every Gmail message ID we've already looked at for a user, so
    re-syncing never reprocesses the same email twice -- this is what makes
    'sync now' safe to click repeatedly, and what a scheduled background
    sync would rely on to stay idempotent.
    """
    __tablename__ = "processed_gmail_messages"
    __table_args__ = (UniqueConstraint("user_id", "gmail_message_id", name="uq_user_gmail_message"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    gmail_message_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    action_taken: Mapped[str] = mapped_column(String(50), nullable=True)  # "created_application", "status_update", "ignored"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
