import csv
import io
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.application import Application, ApplicationStatus
from app.models.company import Company
from app.models.platform import Platform
from app.models.recruiter import Recruiter
from app.models.status_history import StatusHistory
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationOut,
    ApplicationListResponse,
    ApplicationStatusUpdate,
    ApplicationUpdate,
    OfferComparisonItem,
)

router = APIRouter(prefix="/api/applications", tags=["applications"])

# A pipeline stage is "terminal" once it's no longer waiting on anyone --
# no point flagging these for follow-up.
TERMINAL_STATUSES = {
    ApplicationStatus.OFFER_RECEIVED,
    ApplicationStatus.REJECTED,
    ApplicationStatus.WITHDRAWN,
    ApplicationStatus.JOINED,
}
DEFAULT_FOLLOW_UP_DAYS = 7


def _get_or_create_company(db: Session, name: str) -> Company:
    company = db.query(Company).filter(Company.name.ilike(name)).first()
    if not company:
        company = Company(name=name)
        db.add(company)
        db.flush()
    return company


def _get_platform(db: Session, slug: str | None) -> Platform | None:
    if not slug:
        slug = "manual"
    return db.query(Platform).filter(Platform.slug == slug).first()


def _get_or_create_recruiter(db: Session, email: str | None) -> Recruiter | None:
    if not email:
        return None
    recruiter = db.query(Recruiter).filter(Recruiter.email == email).first()
    if not recruiter:
        recruiter = Recruiter(email=email)
        db.add(recruiter)
        db.flush()
    return recruiter


def _get_owned_application(db: Session, application_id: uuid.UUID, user_id: uuid.UUID) -> Application:
    application = (
        db.query(Application)
        .filter(Application.id == application_id, Application.user_id == user_id)
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.post("", response_model=ApplicationOut, status_code=201)
def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.external_application_id:
        existing = (
            db.query(Application)
            .filter(
                Application.user_id == current_user.id,
                Application.external_application_id == payload.external_application_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=409, detail="Application already recorded")

    company = _get_or_create_company(db, payload.company_name)
    platform = _get_platform(db, payload.platform_slug)
    recruiter = _get_or_create_recruiter(db, payload.recruiter_email)
    applied_at = payload.applied_at or datetime.utcnow()

    application = Application(
        user_id=current_user.id,
        company_id=company.id,
        platform_id=platform.id if platform else None,
        recruiter_id=recruiter.id if recruiter else None,
        role_title=payload.role_title,
        job_url=payload.job_url,
        location=payload.location,
        salary_min=payload.salary_min,
        salary_max=payload.salary_max,
        salary_currency=payload.salary_currency,
        work_type=payload.work_type,
        employment_type=payload.employment_type,
        job_description=payload.job_description,
        external_application_id=payload.external_application_id,
        source=payload.source,
        applied_at=applied_at,
        status=ApplicationStatus.APPLIED,
        last_status_change_at=datetime.utcnow(),
        expected_ctc=payload.expected_ctc,
        notice_period_days=payload.notice_period_days,
        referred_by_name=payload.referred_by_name,
        referred_by_email=payload.referred_by_email,
        referred_by_relationship=payload.referred_by_relationship,
        follow_up_at=payload.follow_up_at or (applied_at + timedelta(days=DEFAULT_FOLLOW_UP_DAYS)),
    )
    db.add(application)
    db.flush()

    db.add(
        StatusHistory(
            application_id=application.id,
            from_status=None,
            to_status=ApplicationStatus.APPLIED,
            changed_by=f"system:{payload.source.value}",
        )
    )
    db.commit()
    db.refresh(application)
    return application


@router.get("", response_model=ApplicationListResponse)
def list_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status_filter: ApplicationStatus | None = Query(None, alias="status"),
    company: str | None = None,
    platform_slug: str | None = None,
    keyword: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    query = db.query(Application).filter(Application.user_id == current_user.id)

    if status_filter:
        query = query.filter(Application.status == status_filter)
    if company:
        query = query.join(Company).filter(Company.name.ilike(f"%{company}%"))
    if platform_slug:
        query = query.join(Platform).filter(Platform.slug == platform_slug)
    if keyword:
        query = query.filter(Application.role_title.ilike(f"%{keyword}%"))

    total = query.count()
    items = query.order_by(Application.applied_at.desc()).offset(offset).limit(limit).all()
    return ApplicationListResponse(total=total, items=items)


@router.get("/needs-follow-up", response_model=ApplicationListResponse)
def applications_needing_follow_up(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Applications that are still active (not offered/rejected/withdrawn/joined)
    and whose follow_up_at has passed -- i.e. it's time to nudge the recruiter.
    """
    now = datetime.utcnow()
    query = (
        db.query(Application)
        .filter(
            Application.user_id == current_user.id,
            ~Application.status.in_(TERMINAL_STATUSES),
            Application.follow_up_at.isnot(None),
            Application.follow_up_at <= now,
        )
        .order_by(Application.follow_up_at.asc())
    )
    items = query.all()
    return ApplicationListResponse(total=len(items), items=items)


@router.get("/offers/compare", response_model=list[OfferComparisonItem])
def compare_offers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """All offers received (or joined), side by side, for comparing CTC/notice period/location."""
    rows = (
        db.query(Application)
        .filter(
            Application.user_id == current_user.id,
            Application.status.in_([ApplicationStatus.OFFER_RECEIVED, ApplicationStatus.JOINED]),
        )
        .order_by(Application.offered_ctc.desc().nullslast())
        .all()
    )
    return [
        OfferComparisonItem(
            id=a.id,
            role_title=a.role_title,
            company_name=a.company.name if a.company else None,
            location=a.location,
            work_type=a.work_type,
            status=a.status,
            offered_ctc=a.offered_ctc,
            expected_ctc=a.expected_ctc,
            salary_currency=a.salary_currency,
            notice_period_days=a.notice_period_days,
            applied_at=a.applied_at,
        )
        for a in rows
    ]


@router.get("/export.csv")
def export_applications_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export every logged application as a CSV file for offline records/reporting."""
    applications = (
        db.query(Application)
        .filter(Application.user_id == current_user.id)
        .order_by(Application.applied_at.desc())
        .all()
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "Date Applied", "Company", "Role", "Platform", "Location", "Status",
        "Work Type", "Employment Type", "Expected CTC", "Offered CTC",
        "Notice Period (days)", "Referred By", "Job URL", "Source",
    ])
    for a in applications:
        writer.writerow([
            a.applied_at.strftime("%Y-%m-%d") if a.applied_at else "",
            a.company.name if a.company else "",
            a.role_title,
            a.platform.name if a.platform else "",
            a.location or "",
            a.status.value,
            a.work_type.value,
            a.employment_type.value,
            a.expected_ctc or "",
            a.offered_ctc or "",
            a.notice_period_days or "",
            a.referred_by_name or "",
            a.job_url or "",
            a.source.value,
        ])

    buffer.seek(0)
    filename = f"jobtrack-applications-{datetime.utcnow().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{application_id}", response_model=ApplicationOut)
def get_application(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_owned_application(db, application_id, current_user.id)


@router.patch("/{application_id}", response_model=ApplicationOut)
def update_application(
    application_id: uuid.UUID,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Partial update for editable fields that aren't the pipeline status
    (role, location, CTC, referral info, follow-up date, etc). Status
    changes go through PATCH /{application_id}/status so they're always
    recorded in status_history.
    """
    application = _get_owned_application(db, application_id, current_user.id)

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(application, field, value)

    db.commit()
    db.refresh(application)
    return application


@router.patch("/{application_id}/status", response_model=ApplicationOut)
def update_status(
    application_id: uuid.UUID,
    payload: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = _get_owned_application(db, application_id, current_user.id)

    previous_status = application.status
    application.status = payload.status
    application.last_status_change_at = datetime.utcnow()

    # Once an application reaches a terminal state, there's nothing left
    # to follow up on.
    if payload.status in TERMINAL_STATUSES:
        application.follow_up_at = None

    db.add(
        StatusHistory(
            application_id=application.id,
            from_status=previous_status,
            to_status=payload.status,
            changed_by="user",
            note=payload.note,
        )
    )
    db.commit()
    db.refresh(application)
    return application


@router.delete("/{application_id}", status_code=204)
def delete_application(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = _get_owned_application(db, application_id, current_user.id)
    db.delete(application)
    db.commit()
    return None
