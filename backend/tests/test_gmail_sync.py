"""
Integration test for the Gmail sync orchestration logic. Requires a real
Postgres connection (DATABASE_URL) -- the Gmail API itself is mocked, so
no network access or real Google credentials are needed to run this.

Run with: DATABASE_URL=postgresql://... ENCRYPTION_KEY=... pytest tests/test_gmail_sync.py
"""
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.database import SessionLocal
from app.models.user import User
from app.models.application import Application, ApplicationStatus
from app.models.gmail_sync import ProcessedGmailMessage
from app.core.security import hash_password
from app.core.crypto import encrypt_token
from app.services import gmail_sync

FAKE_MESSAGES = {
    "msg-1": {
        "id": "msg-1", "from": "LinkedIn <jobs-noreply@linkedin.com>",
        "subject": "Your application for Backend Engineer at Acme Corp",
        "date": "Mon, 27 Jul 2026 10:00:00 +0000", "snippet": "...",
        "body_text": "Your application for Backend Engineer at Acme Corp has been received.",
    },
    "msg-2": {
        # Deliberately a different display name than the company stored above --
        # this is what broke naive substring matching before the word-overlap fix.
        "id": "msg-2", "from": '"Acme Corp Recruiting" <hr@acmecorp.com>',
        "subject": "Interview Invitation - Backend Engineer",
        "date": "Tue, 28 Jul 2026 10:00:00 +0000", "snippet": "...",
        "body_text": "We would like to schedule an interview with you for the Backend Engineer role at Acme Corp.",
    },
    "msg-3": {
        "id": "msg-3", "from": "Newsletter <news@randomsite.com>",
        "subject": "10 tips for your career",
        "date": "Wed, 29 Jul 2026 10:00:00 +0000", "snippet": "...",
        "body_text": "Check out our latest blog post.",
    },
}


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def gmail_user(db):
    user = User(
        email=f"gmailtest-{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("secret123"),
        google_refresh_token_encrypted=encrypt_token("fake-refresh-token"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.query(ProcessedGmailMessage).filter(ProcessedGmailMessage.user_id == user.id).delete()
    db.query(Application).filter(Application.user_id == user.id).delete()
    db.delete(user)
    db.commit()


async def _run_sync(db, user):
    async def fake_refresh(refresh_token):
        return {"access_token": "fake-access-token"}

    async def fake_list(access_token, query, max_results=25):
        return list(FAKE_MESSAGES.keys())

    async def fake_get(access_token, message_id):
        return FAKE_MESSAGES[message_id]

    with patch("app.services.gmail_sync.gmail_client.refresh_access_token", new=AsyncMock(side_effect=fake_refresh)), \
         patch("app.services.gmail_sync.gmail_client.list_messages", new=AsyncMock(side_effect=fake_list)), \
         patch("app.services.gmail_sync.gmail_client.get_message", new=AsyncMock(side_effect=fake_get)):
        return await gmail_sync.sync_gmail_for_user(db, user)


@pytest.mark.asyncio
async def test_confirmation_email_creates_application(db, gmail_user):
    result = await _run_sync(db, gmail_user)
    assert result.new_applications == 1
    assert result.ignored == 1

    apps = db.query(Application).filter(Application.user_id == gmail_user.id).all()
    assert len(apps) == 1
    assert apps[0].company.name == "Acme Corp"


@pytest.mark.asyncio
async def test_status_update_matches_despite_different_sender_name(db, gmail_user):
    result = await _run_sync(db, gmail_user)
    assert result.status_updates == 1

    app = db.query(Application).filter(Application.user_id == gmail_user.id).first()
    assert app.status == ApplicationStatus.INTERVIEW_ROUND_1


@pytest.mark.asyncio
async def test_resync_is_idempotent(db, gmail_user):
    await _run_sync(db, gmail_user)
    result2 = await _run_sync(db, gmail_user)

    assert result2.new_applications == 0
    assert result2.status_updates == 0

    apps = db.query(Application).filter(Application.user_id == gmail_user.id).all()
    assert len(apps) == 1  # no duplicate created on re-sync


@pytest.mark.asyncio
async def test_old_email_still_found_after_a_previous_sync_ran(db, gmail_user):
    """
    Regression test for a real bug: once any sync ran and set
    last_gmail_sync_at, an older email that a prior (possibly buggy) sync
    failed to fetch would be permanently invisible to every future sync,
    since the search window was "after: last sync". Sync must always
    re-scan a rolling window and rely on ProcessedGmailMessage for dedup
    instead, so a message that was missed once can still be found later.
    """
    from datetime import datetime, timedelta

    gmail_user.last_gmail_sync_at = datetime.utcnow() - timedelta(hours=2)

    async def fake_refresh(refresh_token):
        return {"access_token": "fake-access-token"}

    async def fake_list(access_token, query, max_results=25):
        assert "after:" not in query, "must not use an after-last-sync watermark"
        return ["msg-1"]  # the confirmation email, "older" than last_gmail_sync_at

    async def fake_get(access_token, message_id):
        return FAKE_MESSAGES["msg-1"]

    with patch("app.services.gmail_sync.gmail_client.refresh_access_token", new=AsyncMock(side_effect=fake_refresh)), \
         patch("app.services.gmail_sync.gmail_client.list_messages", new=AsyncMock(side_effect=fake_list)), \
         patch("app.services.gmail_sync.gmail_client.get_message", new=AsyncMock(side_effect=fake_get)):
        result = await gmail_sync.sync_gmail_for_user(db, gmail_user)

    assert result.new_applications == 1
