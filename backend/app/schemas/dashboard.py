from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_applications: int
    applications_today: int
    applications_this_week: int
    applications_this_month: int
    applications_this_year: int

    success_rate: float
    interview_rate: float
    offer_rate: float
    rejection_rate: float
    response_rate: float
    average_response_time_days: float | None

    most_applied_company: str | None
    most_applied_role: str | None
    most_used_platform: str | None
    needs_follow_up: int


class StatusCount(BaseModel):
    status: str
    count: int


class PlatformCount(BaseModel):
    platform: str
    count: int


class DailyCount(BaseModel):
    date: str
    count: int
