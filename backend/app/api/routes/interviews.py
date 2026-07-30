import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.application import Application
from app.models.interview import InterviewRound
from app.models.user import User
from app.schemas.interview import InterviewRoundCreate, InterviewRoundUpdate, InterviewRoundOut

router = APIRouter(prefix="/api/applications/{application_id}/interviews", tags=["interviews"])


def _get_owned_application(db: Session, application_id: uuid.UUID, user_id: uuid.UUID) -> Application:
    application = (
        db.query(Application)
        .filter(Application.id == application_id, Application.user_id == user_id)
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


@router.get("", response_model=list[InterviewRoundOut])
def list_interview_rounds(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_owned_application(db, application_id, current_user.id)
    return (
        db.query(InterviewRound)
        .filter(InterviewRound.application_id == application_id)
        .order_by(InterviewRound.created_at)
        .all()
    )


@router.post("", response_model=InterviewRoundOut, status_code=201)
def create_interview_round(
    application_id: uuid.UUID,
    payload: InterviewRoundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_owned_application(db, application_id, current_user.id)
    round_ = InterviewRound(application_id=application_id, **payload.model_dump())
    db.add(round_)
    db.commit()
    db.refresh(round_)
    return round_


def _get_owned_round(db: Session, application_id: uuid.UUID, round_id: uuid.UUID, user_id: uuid.UUID) -> InterviewRound:
    _get_owned_application(db, application_id, user_id)
    round_ = (
        db.query(InterviewRound)
        .filter(InterviewRound.id == round_id, InterviewRound.application_id == application_id)
        .first()
    )
    if not round_:
        raise HTTPException(status_code=404, detail="Interview round not found")
    return round_


@router.patch("/{round_id}", response_model=InterviewRoundOut)
def update_interview_round(
    application_id: uuid.UUID,
    round_id: uuid.UUID,
    payload: InterviewRoundUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    round_ = _get_owned_round(db, application_id, round_id, current_user.id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(round_, field, value)
    db.commit()
    db.refresh(round_)
    return round_


@router.delete("/{round_id}", status_code=204)
def delete_interview_round(
    application_id: uuid.UUID,
    round_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    round_ = _get_owned_round(db, application_id, round_id, current_user.id)
    db.delete(round_)
    db.commit()
    return None
