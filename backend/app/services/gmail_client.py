"""
Thin wrapper around Google's OAuth2 and Gmail REST APIs using plain HTTP
calls (httpx) rather than the heavy google-api-python-client SDK -- keeps
the dependency footprint small since we only need a handful of endpoints.
"""
import base64
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx

from app.config import settings

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"

# read-only is all we need -- we never send or modify email
GMAIL_SCOPES = "https://www.googleapis.com/auth/gmail.readonly"


def build_auth_url(state: str) -> str:
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": GMAIL_SCOPES,
        "access_type": "offline",   # required to get a refresh_token
        "prompt": "consent",        # forces refresh_token on every connect, not just the first
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


class GmailAuthError(Exception):
    pass


async def exchange_code_for_tokens(code: str) -> dict:
    """Returns {'access_token', 'refresh_token', 'expires_in', ...} from Google."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        })
    if resp.status_code != 200:
        raise GmailAuthError(f"Token exchange failed: {resp.status_code} {resp.text}")
    return resp.json()


async def refresh_access_token(refresh_token: str) -> dict:
    """Returns a fresh {'access_token', 'expires_in', ...} using a stored refresh_token."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data={
            "refresh_token": refresh_token,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "grant_type": "refresh_token",
        })
    if resp.status_code != 200:
        raise GmailAuthError(f"Token refresh failed: {resp.status_code} {resp.text}")
    return resp.json()


async def list_messages(access_token: str, query: str, max_results: int = 25) -> list[str]:
    """Returns a list of Gmail message IDs matching the search query."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{GMAIL_API_BASE}/messages",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"q": query, "maxResults": max_results},
        )
    if resp.status_code != 200:
        raise GmailAuthError(f"Listing messages failed: {resp.status_code} {resp.text}")
    data = resp.json()
    return [m["id"] for m in data.get("messages", [])]


def _decode_body_part(part: dict) -> str:
    data = part.get("body", {}).get("data")
    if not data:
        return ""
    try:
        return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _extract_plain_text(payload: dict) -> str:
    """Recursively walk a Gmail message payload to find the text/plain (or text/html) body."""
    mime_type = payload.get("mimeType", "")
    if mime_type == "text/plain":
        return _decode_body_part(payload)

    text_fallback = ""
    for part in payload.get("parts", []) or []:
        if part.get("mimeType") == "text/plain":
            text = _decode_body_part(part)
            if text:
                return text
        elif part.get("mimeType") == "text/html" and not text_fallback:
            text_fallback = _decode_body_part(part)
        elif part.get("parts"):
            nested = _extract_plain_text(part)
            if nested:
                return nested
    return text_fallback


async def get_message(access_token: str, message_id: str) -> dict:
    """
    Returns {'id', 'from', 'subject', 'date', 'snippet', 'body_text'} for a
    single Gmail message.
    """
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{GMAIL_API_BASE}/messages/{message_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"format": "full"},
        )
    if resp.status_code != 200:
        raise GmailAuthError(f"Fetching message failed: {resp.status_code} {resp.text}")
    data = resp.json()

    headers = {h["name"].lower(): h["value"] for h in data.get("payload", {}).get("headers", [])}
    body_text = _extract_plain_text(data.get("payload", {})) or data.get("snippet", "")

    return {
        "id": data["id"],
        "from": headers.get("from", ""),
        "subject": headers.get("subject", ""),
        "date": headers.get("date", ""),
        "snippet": data.get("snippet", ""),
        "body_text": body_text,
    }
