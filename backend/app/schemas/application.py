import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.application import ApplicationStatus, WorkType, EmploymentType, DataSource


class ApplicationCreate(BaseModel):
    role_title: str
    company_name: str
    platform_slug: str | None = "manual"
    job_url: str | None = None
    location: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = "INR"
    work_type: WorkType = WorkType.UNKNOWN
    employment_type: EmploymentType = EmploymentType.UNKNOWN
    job_description: str | None = None
    recruiter_email: str | None = None
    external_application_id: str | None = None
    applied_at: datetime | None = None
    source: DataSource = DataSource.MANUAL

    # Compensation & referral -- all optional, relevant to fresher and
    # experienced applicants alike.
    expected_ctc: float | None = None
    notice_period_days: int | None = None
    referred_by_name: str | None = None
    referred_by_email: str | None = None
    referred_by_relationship: str | None = None
    follow_up_at: datetime | None = None  # if omitted, defaults to applied_at + 7 days


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus
    note: str | None = None


class ApplicationUpdate(BaseModel):
    """General-purpose partial update for fields that aren't the pipeline status."""
    role_title: str | None = None
    company_name: str | None = None
    location: str | None = None
    job_url: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    work_type: WorkType | None = None
    employment_type: EmploymentType | None = None
    job_description: str | None = None
    resume_used: str | None = None
    expected_ctc: float | None = None
    offered_ctc: float | None = None
    notice_period_days: int | None = None
    referred_by_name: str | None = None
    referred_by_email: str | None = None
    referred_by_relationship: str | None = None
    follow_up_at: datetime | None = None


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role_title: str
    company_name: str | None
    platform_name: str | None
    job_url: str | None
    location: str | None
    salary_min: float | None
    salary_max: float | None
    salary_currency: str | None
    work_type: WorkType
    employment_type: EmploymentType
    status: ApplicationStatus
    source: DataSource
    applied_at: datetime
    last_status_change_at: datetime | None
    created_at: datetime

    expected_ctc: float | None
    offered_ctc: float | None
    notice_period_days: int | None
    referred_by_name: str | None
    referred_by_email: str | None
    referred_by_relationship: str | None
    follow_up_at: datetime | None


class ApplicationListResponse(BaseModel):
    total: int
    items: list[ApplicationOut]


class OfferComparisonItem(BaseModel):
    id: uuid.UUID
    role_title: str
    company_name: str | None
    location: str | None
    work_type: WorkType
    status: ApplicationStatus
    offered_ctc: float | None
    expected_ctc: float | None
    salary_currency: str | None
    notice_period_days: int | None
    applied_at: datetime
