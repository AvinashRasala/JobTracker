"""Integration tests for the pipeline funnel and upcoming-interviews endpoints."""
import uuid
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def auth_headers():
    email = f"funneltest-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/auth/register", json={"email": email, "password": "secret123"})
    r = client.post("/api/auth/login", data={"username": email, "password": "secret123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_funnel_counts_applications_that_passed_through_each_stage(auth_headers):
    r = client.post("/api/applications", json={"role_title": "A", "company_name": "Acme", "platform_slug": "linkedin"}, headers=auth_headers)
    app1 = r.json()["id"]
    client.patch(f"/api/applications/{app1}/status", json={"status": "interview_round_1"}, headers=auth_headers)

    r = client.post("/api/applications", json={"role_title": "B", "company_name": "Beta", "platform_slug": "naukri"}, headers=auth_headers)
    app2 = r.json()["id"]  # stays at Applied

    r = client.post("/api/applications", json={"role_title": "C", "company_name": "Gamma", "platform_slug": "indeed"}, headers=auth_headers)
    app3 = r.json()["id"]
    client.patch(f"/api/applications/{app3}/status", json={"status": "interview_round_1"}, headers=auth_headers)
    client.patch(f"/api/applications/{app3}/status", json={"status": "offer_received"}, headers=auth_headers)

    r = client.get("/api/dashboard/funnel", headers=auth_headers)
    assert r.status_code == 200
    funnel = {f["stage"]: f["count"] for f in r.json()}

    assert funnel["Applied"] == 3
    assert funnel["Interview"] == 2
    assert funnel["Offer"] == 1


def test_upcoming_interviews_respects_time_window(auth_headers):
    r = client.post("/api/applications", json={"role_title": "Backend Engineer", "company_name": "Acme", "platform_slug": "linkedin"}, headers=auth_headers)
    app_id = r.json()["id"]

    future_time = (datetime.utcnow() + timedelta(hours=5)).isoformat() + "Z"
    r = client.post(f"/api/applications/{app_id}/interviews", json={"round_name": "Technical Round 1", "scheduled_at": future_time}, headers=auth_headers)
    assert r.status_code == 201

    r = client.get("/api/interviews/upcoming?hours=24", headers=auth_headers)
    assert len(r.json()) == 1
    assert r.json()[0]["company_name"] == "Acme"

    r = client.get("/api/interviews/upcoming?hours=1", headers=auth_headers)
    assert len(r.json()) == 0
