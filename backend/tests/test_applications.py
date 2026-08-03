"""
Integration tests for the applications API. Requires a real Postgres
connection (DATABASE_URL).
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def auth_headers():
    email = f"apptest-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/auth/register", json={"email": email, "password": "secret123"})
    assert r.status_code == 201
    r = client.post("/api/auth/login", data={"username": email, "password": "secret123"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_company_name_present_in_create_detail_and_list(auth_headers):
    """
    Regression test: ApplicationOut originally didn't include company_name
    or platform_name at all -- they were only ever sent when *creating* an
    application (typed in by the user), never when reading one back. This
    meant the applications list and detail views had no way to display
    which company an application was for.
    """
    r = client.post(
        "/api/applications",
        json={"role_title": "Senior Backend Engineer", "company_name": "Acme Corp", "platform_slug": "linkedin"},
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    assert r.json()["company_name"] == "Acme Corp"
    assert r.json()["platform_name"] == "LinkedIn Jobs"
    app_id = r.json()["id"]

    r = client.get(f"/api/applications/{app_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["company_name"] == "Acme Corp"
    assert r.json()["platform_name"] == "LinkedIn Jobs"

    r = client.get("/api/applications", headers=auth_headers)
    assert r.status_code == 200
    match = next(item for item in r.json()["items"] if item["id"] == app_id)
    assert match["company_name"] == "Acme Corp"
    assert match["platform_name"] == "LinkedIn Jobs"
