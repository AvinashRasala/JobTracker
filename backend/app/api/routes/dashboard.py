from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.application import Application, ApplicationStatus
from app.models.company import Company
from app.models.platform import Platform
from app.models.status_history import StatusHistory
from app.models.user import User
from app.schemas.dashboard import DashboardStats, StatusCount, PlatformCount, DailyCount, FunnelStage

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

INTERVIEW_STATUSES = {
    ApplicationStatus.INTERVIEW_ROUND_1,
    ApplicationStatus.INTERVIEW_ROUND_2,
    ApplicationStatus.INTERVIEW_ROUND_3,
    ApplicationStatus.HR_INTERVIEW,
    ApplicationStatus.OFFER_RECEIVED,
    ApplicationStatus.JOINED,
}
RESPONSE_STATUSES = {s for s in ApplicationStatus if s != ApplicationStatus.APPLIED}


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    base_query = db.query(Application).filter(Application.user_id == current_user.id)

    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = datetime(now.year, now.month, 1)
    year_start = datetime(now.year, 1, 1)

    total = base_query.count()
    today_count = base_query.filter(Application.applied_at >= today_start).count()
    week_count = base_query.filter(Application.applied_at >= week_start).count()
    month_count = base_query.filter(Application.applied_at >= month_start).count()
    year_count = base_query.filter(Application.applied_at >= year_start).count()

    offers = base_query.filter(Application.status.in_([ApplicationStatus.OFFER_RECEIVED, ApplicationStatus.JOINED])).count()
    interviews = base_query.filter(Application.status.in_(INTERVIEW_STATUSES)).count()
    rejected = base_query.filter(Application.status == ApplicationStatus.REJECTED).count()
    responded = base_query.filter(Application.status.in_(RESPONSE_STATUSES)).count()

    TERMINAL_STATUSES = {
        ApplicationStatus.OFFER_RECEIVED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
        ApplicationStatus.JOINED,
    }
    needs_follow_up = base_query.filter(
        ~Application.status.in_(TERMINAL_STATUSES),
        Application.follow_up_at.isnot(None),
        Application.follow_up_at <= now,
    ).count()

    def pct(part: int, whole: int) -> float:
        return round((part / whole) * 100, 2) if whole else 0.0

    avg_response = (
        db.query(func.avg(StatusHistory.created_at - Application.applied_at))
        .join(Application, Application.id == StatusHistory.application_id)
        .filter(
            Application.user_id == current_user.id,
            StatusHistory.from_status == ApplicationStatus.APPLIED,
        )
        .scalar()
    )
    avg_response_days = round(avg_response.total_seconds() / 86400, 2) if avg_response else None

    most_applied_company = (
        db.query(Company.name, func.count(Application.id).label("cnt"))
        .join(Application, Application.company_id == Company.id)
        .filter(Application.user_id == current_user.id)
        .group_by(Company.name)
        .order_by(func.count(Application.id).desc())
        .first()
    )
    most_applied_role = (
        db.query(Application.role_title, func.count(Application.id).label("cnt"))
        .filter(Application.user_id == current_user.id)
        .group_by(Application.role_title)
        .order_by(func.count(Application.id).desc())
        .first()
    )
    most_used_platform = (
        db.query(Platform.name, func.count(Application.id).label("cnt"))
        .join(Application, Application.platform_id == Platform.id)
        .filter(Application.user_id == current_user.id)
        .group_by(Platform.name)
        .order_by(func.count(Application.id).desc())
        .first()
    )

    return DashboardStats(
        total_applications=total,
        applications_today=today_count,
        applications_this_week=week_count,
        applications_this_month=month_count,
        applications_this_year=year_count,
        success_rate=pct(offers, total),
        interview_rate=pct(interviews, total),
        offer_rate=pct(offers, total),
        rejection_rate=pct(rejected, total),
        response_rate=pct(responded, total),
        average_response_time_days=avg_response_days,
        most_applied_company=most_applied_company[0] if most_applied_company else None,
        most_applied_role=most_applied_role[0] if most_applied_role else None,
        most_used_platform=most_used_platform[0] if most_used_platform else None,
        needs_follow_up=needs_follow_up,
    )


@router.get("/status-distribution", response_model=list[StatusCount])
def status_distribution(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        db.query(Application.status, func.count(Application.id))
        .filter(Application.user_id == current_user.id)
        .group_by(Application.status)
        .all()
    )
    return [StatusCount(status=s.value, count=c) for s, c in rows]


@router.get("/platform-distribution", response_model=list[PlatformCount])
def platform_distribution(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (
        db.query(Platform.name, func.count(Application.id))
        .join(Application, Application.platform_id == Platform.id)
        .filter(Application.user_id == current_user.id)
        .group_by(Platform.name)
        .order_by(func.count(Application.id).desc())
        .all()
    )
    return [PlatformCount(platform=name, count=count) for name, count in rows]


@router.get("/applications-per-day", response_model=list[DailyCount])
def applications_per_day(days: int = 30, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(func.date(Application.applied_at), func.count(Application.id))
        .filter(Application.user_id == current_user.id, Application.applied_at >= since)
        .group_by(func.date(Application.applied_at))
        .order_by(func.date(Application.applied_at))
        .all()
    )
    return [DailyCount(date=str(d), count=c) for d, c in rows]


# Ordered pipeline stages for the funnel chart. Grouped where several raw
# statuses represent the same conceptual stage (e.g. all interview rounds).
FUNNEL_STAGES: list[tuple[str, set[ApplicationStatus]]] = [
    ("Applied", {ApplicationStatus.APPLIED}),
    ("Viewed", {ApplicationStatus.APPLICATION_VIEWED}),
    ("Under Review", {ApplicationStatus.UNDER_REVIEW}),
    ("Assessment", {ApplicationStatus.ASSESSMENT, ApplicationStatus.CODING_TEST}),
    ("Interview", {
        ApplicationStatus.INTERVIEW_ROUND_1, ApplicationStatus.INTERVIEW_ROUND_2,
        ApplicationStatus.INTERVIEW_ROUND_3, ApplicationStatus.HR_INTERVIEW,
    }),
    ("Offer", {ApplicationStatus.OFFER_RECEIVED, ApplicationStatus.JOINED}),
]


@router.get("/funnel", response_model=list[FunnelStage])
def pipeline_funnel(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    For each pipeline stage, counts applications that ever reached that
    stage (via status_history) OR are currently at it -- not just
    "currently at this exact status", since an application that moved on
    to Offer still did pass through Interview.
    """
    results = []
    for label, statuses in FUNNEL_STAGES:
        reached_ids_subquery = (
            db.query(StatusHistory.application_id)
            .filter(StatusHistory.to_status.in_(statuses))
            .subquery()
        )
        count = (
            db.query(Application.id)
            .filter(
                Application.user_id == current_user.id,
                or_(
                    Application.status.in_(statuses),
                    Application.id.in_(db.query(reached_ids_subquery)),
                ),
            )
            .distinct()
            .count()
        )
        results.append(FunnelStage(stage=label, count=count))
    return results
