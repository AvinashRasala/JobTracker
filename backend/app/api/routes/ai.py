import uuid
from datetime import datetime
from functools import wraps

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.application import Application
from app.models.user import User
from app.schemas.ai import MatchScoreOut, CoverLetterOut, FollowUpEmailOut
from app.services import ai_features
from app.services.openai_client import OpenAINotConfiguredError, OpenAIRequestError

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _get_owned_application(db: Session, application_id: uuid.UUID, user_id: uuid.UUID) -> Application:
    application = (
        db.query(Application)
        .filter(Application.id == application_id, Application.user_id == user_id)
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


def _handle_ai_errors(fn):
    """Shared error mapping so every AI route responds consistently."""
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except OpenAINotConfiguredError as e:
            raise HTTPException(status_code=503, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except OpenAIRequestError as e:
            raise HTTPException(status_code=502, detail=f"AI request failed: {e}")
    return wrapper


@router.post("/match-score/{application_id}", response_model=MatchScoreOut)
@_handle_ai_errors
async def match_score(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = _get_owned_application(db, application_id, current_user.id)
    result = await ai_features.get_match_score(
        role_title=application.role_title,
        company_name=application.company_name or "the company",
        job_description=application.job_description,
        resume_text=current_user.resume_text,
    )
    return MatchScoreOut(
        score=result.score,
        explanation=result.explanation,
        matching_skills=result.matching_skills,
        missing_skills=result.missing_skills,
    )


@router.post("/cover-letter/{application_id}", response_model=CoverLetterOut)
@_handle_ai_errors
async def cover_letter(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = _get_owned_application(db, application_id, current_user.id)
    letter = await ai_features.generate_cover_letter(
        role_title=application.role_title,
        company_name=application.company_name or "the company",
        job_description=application.job_description,
        resume_text=current_user.resume_text,
        applicant_name=current_user.full_name or "the applicant",
    )
    return CoverLetterOut(cover_letter=letter)


@router.post("/follow-up-email/{application_id}", response_model=FollowUpEmailOut)
@_handle_ai_errors
async def follow_up_email(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = _get_owned_application(db, application_id, current_user.id)
    days_ago = (datetime.utcnow() - application.applied_at).days
    email_text = await ai_features.generate_follow_up_email(
        role_title=application.role_title,
        company_name=application.company_name or "the company",
        applied_days_ago=max(days_ago, 0),
        applicant_name=current_user.full_name or "the applicant",
        current_status=application.status.value,
    )
    return FollowUpEmailOut(email=email_text)
