"""Integration tests for document upload/list/delete/attach. Requires DATABASE_URL."""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def auth_headers():
    email = f"doctest-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/auth/register", json={"email": email, "password": "secret123"})
    assert r.status_code == 201
    r = client.post("/api/auth/login", data={"username": email, "password": "secret123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_upload_serve_list_attach_delete(auth_headers):
    fake_pdf = b"%PDF-1.4 fake content" + b"0" * 100
    r = client.post(
        "/api/documents",
        data={"label": "Resume - Backend focus", "document_type": "resume"},
        files={"file": ("resume.pdf", fake_pdf, "application/pdf")},
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    doc_id = r.json()["id"]

    r = client.get(r.json()["file_path"])
    assert r.status_code == 200

    r = client.get("/api/documents", headers=auth_headers)
    assert len(r.json()) == 1

    r = client.post(
        "/api/applications",
        json={"role_title": "Backend Engineer", "company_name": "Acme Corp", "platform_slug": "linkedin"},
        headers=auth_headers,
    )
    app_id = r.json()["id"]
    r = client.patch(f"/api/applications/{app_id}", json={"resume_document_id": doc_id}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["resume_document_label"] == "Resume - Backend focus"

    r = client.delete(f"/api/documents/{doc_id}", headers=auth_headers)
    assert r.status_code == 204

    r = client.get("/api/documents", headers=auth_headers)
    assert len(r.json()) == 0
