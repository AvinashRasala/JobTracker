import enum
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class InterviewMode(str, enum.Enum):
    PHONE = "phone"
    VIDEO = "video"
    ONSITE = "onsite"
    ASSESSMENT = "assessment"  # take-home / online coding test, no live interviewer
    OTHER = "other"


class InterviewOutcome(str, enum.Enum):
    PENDING = "pending"
    CLEARED = "cleared"
    REJECTED = "rejected"
    RESCHEDULED = "rescheduled"
    NO_SHOW = "no_show"


_values_callable = lambda enum_cls: [e.value for e in enum_cls]


class InterviewRound(Base):
    """
    One row per interview round for an application -- phone screen,
    technical round 1, onsite, HR, etc. Kept separate from
    Application.status (which tracks the pipeline stage) so a full
    history of rounds/feedback survives even after the application's
    overall status moves on.
    """
    __tablename__ = "interview_rounds"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )

    round_name: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g. "Technical Round 1", "HR Discussion"
    mode: Mapped[InterviewMode] = mapped_column(
        SAEnum(InterviewMode, name="interview_mode", values_callable=_values_callable),
        default=InterviewMode.VIDEO,
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    interviewer_name: Mapped[str] = mapped_column(String(255), nullable=True)
    interviewer_designation: Mapped[str] = mapped_column(String(255), nullable=True)
    feedback: Mapped[str] = mapped_column(Text, nullable=True)
    outcome: Mapped[InterviewOutcome] = mapped_column(
        SAEnum(InterviewOutcome, name="interview_outcome", values_callable=_values_callable),
        default=InterviewOutcome.PENDING,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    application: Mapped["Application"] = relationship(back_populates="interview_rounds")
