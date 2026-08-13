"""
Tests for AI features: response parsing (fully offline) and API endpoint
error handling / success path (OpenAI calls mocked -- no real API key or
network access needed).
"""
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.ai_features import parse_match_score_response

client = TestClient(app)


@pytest.mark.parametrize("raw,expected_score", [
    ('{"score": 85, "explanation": "Good match.", "matching_skills": ["Python"], "missing_skills": []}', 85),
    ('```json\n{"score": 60, "explanation": "OK.", "matching_skills": [], "missing_skills": ["Go"]}\n```', 60),
    ('{"score": 150, "explanation": "test", "matching_skills": [], "missing_skills": []}', 100),
    ('{"score": -10, "explanation": "test", "matching_skills": [], "missing_skills": []}', 0),
])
def test_parse_match_score_response(raw, expected_score):
    result = parse_match_score_response(raw)
    assert result.score == expected_score


def test_parse_match_score_response_rejects_garbage():
    with pytest.raises(ValueError):
        parse_match_score_response("I cannot help with that request.")


@pytest.fixture
def auth_headers_and_app():
    email = f"aitest-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/auth/register", json={"email": email, "password": "secret123"})
    r = client.post("/api/auth/login", data={"username": email, "password": "secret123"})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    r = client.post(
        "/api/applications",
        json={
            "role_title": "Backend Engineer", "company_name": "Acme Corp", "platform_slug": "linkedin",
            "job_description": "Python backend engineer with SQL experience.",
        },
        headers=headers,
    )
    return headers, r.json()["id"]


def test_match_score_requires_resume_text(auth_headers_and_app):
    headers, app_id = auth_headers_and_app
    r = client.post(f"/api/ai/match-score/{app_id}", headers=headers)
    assert r.status_code == 400


def test_match_score_without_api_key_returns_503(auth_headers_and_app):
    headers, app_id = auth_headers_and_app
    client.patch("/api/auth/me", json={"resume_text": "5 years Python, SQL."}, headers=headers)
    r = client.post(f"/api/ai/match-score/{app_id}", headers=headers)
    assert r.status_code == 503


def test_match_score_success_with_mocked_openai(auth_headers_and_app):
    headers, app_id = auth_headers_and_app
    client.patch("/api/auth/me", json={"resume_text": "5 years Python, SQL."}, headers=headers)

    fake = '{"score": 78, "explanation": "Good overlap.", "matching_skills": ["Python"], "missing_skills": ["K8s"]}'
    with patch("app.services.ai_features.openai_client.chat_completion", new=AsyncMock(return_value=fake)):
        r = client.post(f"/api/ai/match-score/{app_id}", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["score"] == 78


def test_cover_letter_and_follow_up_email_success(auth_headers_and_app):
    headers, app_id = auth_headers_and_app
    client.patch("/api/auth/me", json={"resume_text": "5 years Python, SQL."}, headers=headers)

    with patch("app.services.ai_features.openai_client.chat_completion", new=AsyncMock(return_value="Dear Hiring Manager, ...")):
        r = client.post(f"/api/ai/cover-letter/{app_id}", headers=headers)
        assert r.status_code == 200
        assert "cover_letter" in r.json()

        r = client.post(f"/api/ai/follow-up-email/{app_id}", headers=headers)
        assert r.status_code == 200
        assert "email" in r.json()
