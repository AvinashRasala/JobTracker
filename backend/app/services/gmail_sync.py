"""
Orchestrates a Gmail sync for one user: search for job-related emails,
parse each new one, and either create an application (confirmation emails)
or update an existing one's status (interview/offer/rejection emails).

The gmail_client calls are imported as module references (not passed in)
so tests can monkeypatch `app.services.gmail_client.list_messages` /
`get_message` / `refresh_access_token` with fixtures instead of hitting
the real Google API.
"""
import re
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.crypto import decrypt_token, encrypt_token
from app.models.application import Application, ApplicationStatus, DataSource
from app.models.company import Company
from app.models.gmail_sync import ProcessedGmailMessage
from app.models.platform import Platform
from app.models.status_history import StatusHistory
from app.models.user import User
from app.services import gmail_client
from app.services.email_parser import parse_email

# Reasonably broad net -- better to over-fetch and let per-message parsing
# filter out noise than to miss a real application email with too narrow
# a search.
# Every term is a quoted exact phrase, not a bare word. Bare words like
# "application", "offer", or especially "unfortunately" match almost any
# email (job-alert digests are full of "Easy Apply" buttons; "unfortunately"
# appears in all kinds of unrelated correspondence) -- this both crowds
# genuine confirmation emails out of the result window AND, worse, gets
# misclassified as a real status update and silently applied to the wrong
# application. Every phrase here matches the same phrasing the classifier
# in email_parser.py actually looks for, so nothing gets fetched that
# couldn't also be correctly classified.
GMAIL_SEARCH_QUERY = (
    '("thank you for applying" OR "application received" OR "application confirmed" OR '
    '"application successful" OR "we have received your application" OR '
    '"application submitted" OR "your application" OR '
    '"schedule an interview" OR "interview invitation" OR "would like to interview" OR '
    '"technical interview" OR "coding challenge" OR "online assessment" OR '
    '"skills assessment" OR "complete an assessment" OR '
    '"pleased to offer" OR "job offer" OR "offer letter" OR "extend an offer" OR '
    '"regret to inform" OR "not moving forward" OR "will not be proceeding" OR '
    '"decided not to move forward" OR "not selected") '
    "-from:jobalerts-noreply@linkedin.com "
    "-from:jobalert.indeed.com "
    "-from:no-reply-chat@updates.internshala.com"
)
GMAIL_MAX_RESULTS = 100
SYNC_WINDOW_DAYS = 30  # always searches this many days back, every sync -- see comment below

TERMINAL_STATUSES = {
    ApplicationStatus.OFFER_RECEIVED,
    ApplicationStatus.REJECTED,
    ApplicationStatus.WITHDRAWN,
    ApplicationStatus.JOINED,
}

# Words that appear in company-adjacent email display names but don't
# actually identify the company (e.g. "Acme Corp Recruiting" should still
# match a stored company named "Acme Corp").
_GENERIC_COMPANY_WORDS = {
    "recruiting", "recruitment", "careers", "career", "talent", "team",
    "hr", "hiring", "jobs", "inc", "llc", "ltd", "corp", "corporation", "co",
    "the", "group", "hiring team", "people",
}


def _normalize_company_words(name: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", name.lower())
    return {w for w in words if w not in _GENERIC_COMPANY_WORDS and len(w) > 1}


def _find_matching_application(db: Session, user_id, parsed_company_name: str) -> Application | None:
    """
    Finds the most recent non-terminal application whose company shares at
    least one meaningful (non-generic) word with the parsed sender name --
    a plain substring match breaks the moment a recruiter's display name
    has extra words like "Recruiting" or "Talent Team" tacked on.
    """
    target_words = _normalize_company_words(parsed_company_name)
    if not target_words:
        return None

    candidates = (
        db.query(Application)
        .join(Company)
        .filter(Application.user_id == user_id, ~Application.status.in_(TERMINAL_STATUSES))
        .order_by(Application.applied_at.desc())
        .all()
    )
    for application in candidates:
        if not application.company:
            continue
        if target_words & _normalize_company_words(application.company.name):
            return application
    return None


@dataclass
class SyncResult:
    new_applications: int = 0
    status_updates: int = 0
    ignored: int = 0
    errors: list[str] = field(default_factory=list)


def _build_platform_domain_map(db: Session) -> dict[str, str]:
    platforms = db.query(Platform).filter(Platform.email_domain_pattern.isnot(None)).all()
    return {p.email_domain_pattern: p.slug for p in platforms}


def _get_or_create_company(db: Session, name: str) -> Company:
    company = db.query(Company).filter(Company.name.ilike(name)).first()
    if not company:
        company = Company(name=name)
        db.add(company)
        db.flush()
    return company


def _get_platform(db: Session, slug: str | None) -> Platform | None:
    if not slug:
        return db.query(Platform).filter(Platform.slug == "manual").first()
    return db.query(Platform).filter(Platform.slug == slug).first()


async def sync_gmail_for_user(db: Session, user: User) -> SyncResult:
    result = SyncResult()

    if not user.google_refresh_token_encrypted:
        result.errors.append("Gmail is not connected for this user.")
        return result

    refresh_token = decrypt_token(user.google_refresh_token_encrypted)
    token_data = await gmail_client.refresh_access_token(refresh_token)
    access_token = token_data["access_token"]
    # Google may rotate the refresh token itself on refresh; store the new one if given.
    if token_data.get("refresh_token"):
        user.google_refresh_token_encrypted = encrypt_token(token_data["refresh_token"])
    user.google_access_token_encrypted = encrypt_token(access_token)

    # Always search a rolling window rather than "since last sync". An
    # incremental after-last-sync watermark sounds more efficient, but has
    # a real failure mode: if an earlier sync's search missed a message
    # (e.g. it got crowded out of the result window, or the query wasn't
    # matching what it should have), the watermark still advances past it,
    # permanently excluding that message from every future sync. Since
    # ProcessedGmailMessage already makes re-scanning the same window safe
    # (already-processed messages are skipped before any extra API call),
    # there's no correctness reason to use "after: last sync" here.
    query = f"{GMAIL_SEARCH_QUERY} newer_than:{SYNC_WINDOW_DAYS}d"

    message_ids = await gmail_client.list_messages(access_token, query, max_results=GMAIL_MAX_RESULTS)
    platform_domain_map = _build_platform_domain_map(db)

    already_processed = {
        row.gmail_message_id
        for row in db.query(ProcessedGmailMessage).filter(
            ProcessedGmailMessage.user_id == user.id,
            ProcessedGmailMessage.gmail_message_id.in_(message_ids),
        )
    } if message_ids else set()

    for message_id in message_ids:
        if message_id in already_processed:
            continue

        try:
            message = await gmail_client.get_message(access_token, message_id)
            parsed = parse_email(message["from"], message["subject"], message["body_text"], platform_domain_map)
            action = "ignored"

            if parsed.kind == "confirmation":
                existing = (
                    db.query(Application)
                    .filter(Application.user_id == user.id, Application.source_email_id == message_id)
                    .first()
                )
                if not existing:
                    company = _get_or_create_company(db, parsed.company_name)
                    platform = _get_platform(db, parsed.platform_slug)
                    application = Application(
                        user_id=user.id,
                        company_id=company.id,
                        platform_id=platform.id if platform else None,
                        role_title=parsed.role_title,
                        source=DataSource.GMAIL_PARSER,
                        source_email_id=message_id,
                        applied_at=datetime.utcnow(),
                        status=ApplicationStatus.APPLIED,
                        last_status_change_at=datetime.utcnow(),
                    )
                    db.add(application)
                    db.flush()
                    db.add(StatusHistory(
                        application_id=application.id,
                        from_status=None,
                        to_status=ApplicationStatus.APPLIED,
                        changed_by="system:gmail_parser",
                    ))
                    result.new_applications += 1
                    action = "created_application"

            elif parsed.kind == "status_update" and parsed.new_status:
                candidate = _find_matching_application(db, user.id, parsed.company_name)
                if candidate:
                    previous_status = candidate.status
                    candidate.status = parsed.new_status
                    candidate.last_status_change_at = datetime.utcnow()
                    if parsed.new_status in TERMINAL_STATUSES:
                        candidate.follow_up_at = None
                    db.add(StatusHistory(
                        application_id=candidate.id,
                        from_status=previous_status,
                        to_status=parsed.new_status,
                        changed_by="system:gmail_parser",
                        note=f"Detected from email: {message['subject']}",
                    ))
                    result.status_updates += 1
                    action = "status_update"

            if action == "ignored":
                result.ignored += 1

            db.add(ProcessedGmailMessage(
                user_id=user.id,
                gmail_message_id=message_id,
                action_taken=action,
                subject=message["subject"][:500] if message.get("subject") else None,
                sender=message["from"][:255] if message.get("from") else None,
            ))
            db.commit()
        except Exception as e:  # noqa: BLE001 -- one bad message shouldn't abort the whole sync
            db.rollback()
            result.errors.append(f"{message_id}: {e}")

    user.last_gmail_sync_at = datetime.utcnow()
    db.commit()
    return result
