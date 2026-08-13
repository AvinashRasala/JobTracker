import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.interview import InterviewMode, InterviewOutcome


class InterviewRoundCreate(BaseModel):
    round_name: str
    mode: InterviewMode = InterviewMode.VIDEO
    scheduled_at: datetime | None = None
    interviewer_name: str | None = None
    interviewer_designation: str | None = None
    feedback: str | None = None
    outcome: InterviewOutcome = InterviewOutcome.PENDING


class InterviewRoundUpdate(BaseModel):
    round_name: str | None = None
    mode: InterviewMode | None = None
    scheduled_at: datetime | None = None
    interviewer_name: str | None = None
    interviewer_designation: str | None = None
    feedback: str | None = None
    outcome: InterviewOutcome | None = None


class InterviewRoundOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    application_id: uuid.UUID
    round_name: str
    mode: InterviewMode
    scheduled_at: datetime | None
    interviewer_name: str | None
    interviewer_designation: str | None
    feedback: str | None
    outcome: InterviewOutcome
    created_at: datetime
    updated_at: datetime


class UpcomingInterviewOut(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    role_title: str
    company_name: str | None
    round_name: str
    scheduled_at: datetime
