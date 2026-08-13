import enum
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Numeric, Integer, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ApplicationStatus(str, enum.Enum):
    APPLIED = "applied"
    APPLICATION_VIEWED = "application_viewed"
    UNDER_REVIEW = "under_review"
    ASSESSMENT = "assessment"
    CODING_TEST = "coding_test"
    INTERVIEW_ROUND_1 = "interview_round_1"
    INTERVIEW_ROUND_2 = "interview_round_2"
    INTERVIEW_ROUND_3 = "interview_round_3"
    HR_INTERVIEW = "hr_interview"
    OFFER_RECEIVED = "offer_received"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    JOINED = "joined"


class WorkType(str, enum.Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    UNKNOWN = "unknown"


class EmploymentType(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"
    UNKNOWN = "unknown"


class DataSource(str, enum.Enum):
    GMAIL_PARSER = "gmail_parser"
    CHROME_EXTENSION = "chrome_extension"
    MANUAL = "manual"


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True, index=True)
    platform_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("platforms.id"), nullable=True, index=True)
    recruiter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recruiters.id"), nullable=True)

    role_title: Mapped[str] = mapped_column(String(255), nullable=False)
    job_url: Mapped[str] = mapped_column(String(1000), nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    salary_min: Mapped[float] = mapped_column(Numeric(12, 2), nullable=True)
    salary_max: Mapped[float] = mapped_column(Numeric(12, 2), nullable=True)
    salary_currency: Mapped[str] = mapped_column(String(10), nullable=True, default="INR")

    work_type: Mapped[WorkType] = mapped_column(
        SAEnum(WorkType, name="work_type", values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        default=WorkType.UNKNOWN,
    )
    employment_type: Mapped[EmploymentType] = mapped_column(
        SAEnum(EmploymentType, name="employment_type", values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        default=EmploymentType.UNKNOWN,
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(ApplicationStatus, name="application_status", values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        default=ApplicationStatus.APPLIED,
        index=True,
    )

    external_application_id: Mapped[str] = mapped_column(String(255), nullable=True)
    job_description: Mapped[str] = mapped_column(Text, nullable=True)
    resume_used: Mapped[str] = mapped_column(String(500), nullable=True)  # free-text note, kept for backward compat
    resume_document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    cover_letter_document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)

    # Compensation & offer tracking -- useful for both a fresher's first
    # offer and an experienced hire comparing multiple offers.
    expected_ctc: Mapped[float] = mapped_column(Numeric(12, 2), nullable=True)
    offered_ctc: Mapped[float] = mapped_column(Numeric(12, 2), nullable=True)
    notice_period_days: Mapped[int] = mapped_column(Integer, nullable=True)

    # Referral tracking
    referred_by_name: Mapped[str] = mapped_column(String(255), nullable=True)
    referred_by_email: Mapped[str] = mapped_column(String(255), nullable=True)
    referred_by_relationship: Mapped[str] = mapped_column(String(100), nullable=True)  # e.g. "Ex-colleague", "Friend"

    # Follow-up reminders: when to next nudge the recruiter/check in.
    # Defaults to applied_at + 7 days if not set explicitly (see applications.py).
    follow_up_at: Mapped[datetime] = mapped_column(DateTime, nullable=True, index=True)

    source: Mapped[DataSource] = mapped_column(
        SAEnum(DataSource, name="data_source", values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        default=DataSource.MANUAL,
    )
    source_email_id: Mapped[str] = mapped_column(String(255), nullable=True)

    applied_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    last_status_change_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="applications")
    company: Mapped["Company"] = relationship(back_populates="applications")
    platform: Mapped["Platform"] = relationship(back_populates="applications")
    recruiter: Mapped["Recruiter"] = relationship(back_populates="applications")
    status_history: Mapped[list["StatusHistory"]] = relationship(back_populates="application", cascade="all, delete-orphan")
    notes: Mapped[list["Note"]] = relationship(back_populates="application", cascade="all, delete-orphan")
    interview_rounds: Mapped[list["InterviewRound"]] = relationship(
        back_populates="application", cascade="all, delete-orphan", order_by="InterviewRound.created_at"
    )
    resume_document: Mapped["Document"] = relationship(foreign_keys=[resume_document_id])
    cover_letter_document: Mapped["Document"] = relationship(foreign_keys=[cover_letter_document_id])

    @property
    def resume_document_label(self) -> str | None:
        return self.resume_document.label if self.resume_document else None

    @property
    def cover_letter_document_label(self) -> str | None:
        return self.cover_letter_document.label if self.cover_letter_document else None

    @property
    def company_name(self) -> str | None:
        """Convenience accessor so ApplicationOut can expose company_name
        directly (Pydantic's from_attributes reads this like any other
        attribute) without every route having to flatten it manually."""
        return self.company.name if self.company else None

    @property
    def platform_name(self) -> str | None:
        return self.platform.name if self.platform else None
