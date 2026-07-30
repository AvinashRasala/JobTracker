"""
Heuristic parser for job-related emails: decides whether an email is an
application confirmation or a status update, and tries to pull out the
company name, role title, and platform.

This is inherently approximate -- job platforms and companies don't follow
one template. Patterns here cover the common phrasings; anything that
doesn't match falls back to using the subject line / sender name rather
than being silently dropped, since a rough auto-logged entry the user can
edit is more useful than nothing.
"""
import re
from dataclasses import dataclass

from app.models.application import ApplicationStatus

# --- Status/kind detection, ordered by priority (checked top to bottom) ---
_CONFIRMATION_PHRASES = [
    "application has been received",
    "application received",
    "application submitted",
    "your application was sent",
    "your application to",
    "your application for",
    "thanks for applying",
    "thank you for applying",
    "thanks for your interest",
    "we have received your application",
    "we've received your application",
    "application successfully submitted",
    "application successful",
    "application sent",
    "you have successfully applied",
    "successfully applied",
]

# Each entry: (keywords to look for in subject+body, resulting status)
_STATUS_RULES: list[tuple[list[str], ApplicationStatus | None]] = [
    (["pleased to offer", "job offer", "offer letter", "excited to offer", "extend an offer"], ApplicationStatus.OFFER_RECEIVED),
    (["unfortunately", "not moving forward", "will not be proceeding", "regret to inform",
      "decided not to move forward", "other candidates", "not selected", "unable to offer"], ApplicationStatus.REJECTED),
    (["schedule an interview", "interview invitation", "would like to interview",
      "next round", "technical interview", "interview with"], ApplicationStatus.INTERVIEW_ROUND_1),
    (["coding challenge", "online assessment", "take-home assignment", "skills assessment",
      "complete an assessment"], ApplicationStatus.ASSESSMENT),
    (_CONFIRMATION_PHRASES, None),  # confirmation, not a status change
]

# --- Company/role extraction patterns, tried in order against the subject line ---
_SUBJECT_PATTERNS = [
    re.compile(r"your application for (?P<role>.+?) at (?P<company>.+?)(?:\s*[-|]|$)", re.IGNORECASE),
    re.compile(r"thank you for applying to (?P<role>.+?) at (?P<company>.+?)(?:\s*[-|]|$)", re.IGNORECASE),
    re.compile(r"application (?:submitted|confirmation|received) for (?P<role>.+?) at (?P<company>.+?)(?:\s*[-|]|$)", re.IGNORECASE),
    re.compile(r"application (?:confirmation|received|submitted)\s*[-:]\s*(?P<role>.+?) at (?P<company>.+?)(?:\s*[-|]|$)", re.IGNORECASE),
    re.compile(r"application for (?P<role>.+?) at (?P<company>.+?)(?:\s*[-|]|$)", re.IGNORECASE),
    re.compile(r"your application (?:was sent to|to)\s*(?P<company>.+?)(?:\s*[-|:]|$)", re.IGNORECASE),
    re.compile(r"^(?P<company>.+?)\s*[-:]\s*application (?:received|confirmation|submitted)", re.IGNORECASE),
    # Generic last resort: "<role> at <company>" anywhere in the subject.
    re.compile(r"(?P<role>.+?)\s+at\s+(?P<company>.+?)(?:\s*[-|]|$)", re.IGNORECASE),
]


@dataclass
class ParsedEmail:
    kind: str  # "confirmation" | "status_update" | "unrelated"
    platform_slug: str | None
    company_name: str | None
    role_title: str | None
    new_status: ApplicationStatus | None


def _match_platform(from_addr: str, platform_domain_map: dict[str, str]) -> str | None:
    from_lower = from_addr.lower()
    for domain_fragment, slug in platform_domain_map.items():
        if domain_fragment and domain_fragment.lower() in from_lower:
            return slug
    return None


def _extract_sender_display_name(from_addr: str) -> str | None:
    # "Acme Corp Careers <noreply@acme.com>" -> "Acme Corp Careers"
    match = re.match(r'^"?([^"<]+?)"?\s*<', from_addr)
    if match:
        name = match.group(1).strip()
        return name or None
    return None


def _extract_company_role(subject: str, from_addr: str) -> tuple[str | None, str | None]:
    for pattern in _SUBJECT_PATTERNS:
        match = pattern.search(subject)
        if match:
            groups = match.groupdict()
            company = groups.get("company", "").strip(" .-\u2013\u2014") or None
            role = groups.get("role", "").strip(" .-\u2013\u2014") or None
            if company:
                return company, role
    # Fallback: use the sender's display name as the company if it doesn't
    # look like a generic platform name (those are matched separately).
    display_name = _extract_sender_display_name(from_addr)
    return display_name, None


def parse_email(from_addr: str, subject: str, body_text: str, platform_domain_map: dict[str, str]) -> ParsedEmail:
    haystack = f"{subject}\n{body_text}".lower()

    platform_slug = _match_platform(from_addr, platform_domain_map)

    matched_status: ApplicationStatus | None = None
    matched_kind = "unrelated"

    for keywords, status in _STATUS_RULES:
        if any(kw in haystack for kw in keywords):
            if status is None:
                matched_kind = "confirmation"
            else:
                matched_kind = "status_update"
                matched_status = status
            break

    if matched_kind == "unrelated":
        return ParsedEmail(kind="unrelated", platform_slug=platform_slug, company_name=None, role_title=None, new_status=None)

    company_name, role_title = _extract_company_role(subject, from_addr)

    if not role_title:
        # Fall back to a trimmed subject line rather than leaving it blank --
        # the user can always edit it from the application detail page.
        role_title = re.sub(r"^(re:|fwd:)\s*", "", subject, flags=re.IGNORECASE).strip() or "Unknown role"

    if not company_name:
        company_name = _extract_sender_display_name(from_addr) or from_addr.split("@")[-1].split(">")[0]

    return ParsedEmail(
        kind=matched_kind,
        platform_slug=platform_slug,
        company_name=company_name,
        role_title=role_title,
        new_status=matched_status,
    )
