from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import settings
from app.core.crypto import encrypt_token
from app.core.security import decode_access_token, create_access_token
from app.database import get_db
from app.models.application import Application
from app.models.gmail_sync import ProcessedGmailMessage
from app.models.status_history import StatusHistory
from app.models.user import User
from app.schemas.gmail import GmailStatus, GmailSyncResult, GmailAuthUrl, GmailStatusChange, GmailSkippedEmail
from app.services import gmail_client
from app.services.gmail_sync import sync_gmail_for_user

router = APIRouter(prefix="/api/gmail", tags=["gmail"])


@router.get("/connect", response_model=GmailAuthUrl)
def start_gmail_connect(current_user: User = Depends(get_current_user)):
    """
    Returns a Google OAuth consent URL. The frontend redirects the browser
    here; we encode the user's own JWT as the OAuth 'state' parameter so
    the callback (which Google calls directly, with no Authorization
    header) knows which account to attach the tokens to.
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Gmail integration isn't configured on this server yet (missing Google OAuth credentials).",
        )
    # Reuse the user's existing bearer token as opaque state; it's already
    # a signed JWT so it can't be tampered with in transit.
    state_token = create_access_token(subject=str(current_user.id), expires_minutes=10)
    return GmailAuthUrl(auth_url=gmail_client.build_auth_url(state_token))


@router.get("/callback")
async def gmail_oauth_callback(code: str, state: str, db: Session = Depends(get_db)):
    """
    Google redirects here after the user approves access. No Authorization
    header is available (Google calls this directly), so we recover the
    user from the signed 'state' token instead.
    """
    user_id = decode_access_token(state)
    if not user_id:
        return RedirectResponse(f"{settings.FRONTEND_URL}/settings?gmail=error")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse(f"{settings.FRONTEND_URL}/settings?gmail=error")

    try:
        tokens = await gmail_client.exchange_code_for_tokens(code)
    except gmail_client.GmailAuthError:
        return RedirectResponse(f"{settings.FRONTEND_URL}/settings?gmail=error")

    if not tokens.get("refresh_token"):
        # Happens if the user had already granted access before and Google
        # didn't re-issue a refresh_token. Ask them to disconnect + reconnect.
        return RedirectResponse(f"{settings.FRONTEND_URL}/settings?gmail=no_refresh_token")

    user.google_access_token_encrypted = encrypt_token(tokens["access_token"])
    user.google_refresh_token_encrypted = encrypt_token(tokens["refresh_token"])
    db.commit()

    return RedirectResponse(f"{settings.FRONTEND_URL}/settings?gmail=connected")


@router.get("/status", response_model=GmailStatus)
def gmail_status(current_user: User = Depends(get_current_user)):
    return GmailStatus(
        connected=bool(current_user.google_refresh_token_encrypted),
        last_synced_at=current_user.last_gmail_sync_at,
    )


@router.post("/sync", response_model=GmailSyncResult)
async def gmail_sync(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.google_refresh_token_encrypted:
        raise HTTPException(status_code=400, detail="Gmail is not connected. Connect it first from Settings.")
    result = await sync_gmail_for_user(db, current_user)
    return GmailSyncResult(
        new_applications=result.new_applications,
        status_updates=result.status_updates,
        ignored=result.ignored,
        errors=result.errors,
    )


@router.delete("/disconnect", status_code=204)
def gmail_disconnect(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.google_access_token_encrypted = None
    current_user.google_refresh_token_encrypted = None
    current_user.last_gmail_sync_at = None
    db.commit()
    return None


@router.get("/recent-changes", response_model=list[GmailStatusChange])
def gmail_recent_changes(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Every status change the Gmail sync has made for this user, most recent
    first -- lets you audit (and, from the applications list, manually
    revert via the status dropdown) anything that got misclassified.
    """
    rows = (
        db.query(StatusHistory, Application)
        .join(Application, Application.id == StatusHistory.application_id)
        .filter(Application.user_id == current_user.id, StatusHistory.changed_by == "system:gmail_parser")
        .order_by(StatusHistory.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        GmailStatusChange(
            status_history_id=history.id,
            application_id=application.id,
            role_title=application.role_title,
            company_name=application.company.name if application.company else None,
            from_status=history.from_status.value if history.from_status else None,
            to_status=history.to_status.value,
            note=history.note,
            created_at=history.created_at,
        )
        for history, application in rows
    ]


@router.get("/skipped-emails", response_model=list[GmailSkippedEmail])
def gmail_skipped_emails(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Emails the sync found but deliberately didn't act on -- either they
    didn't match a specific enough confirmation/status phrase, or they
    looked like a status update but couldn't be confidently matched to any
    existing application. Shown so you can judge for yourself whether
    anything real is being missed.
    """
    rows = (
        db.query(ProcessedGmailMessage)
        .filter(ProcessedGmailMessage.user_id == current_user.id, ProcessedGmailMessage.action_taken == "ignored")
        .order_by(ProcessedGmailMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        GmailSkippedEmail(gmail_message_id=row.gmail_message_id, subject=row.subject, sender=row.sender, created_at=row.created_at)
        for row in rows
    ]
