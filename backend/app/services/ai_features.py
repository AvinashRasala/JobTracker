"""
AI-powered features: resume match scoring, cover letter generation, and
follow-up email drafting. Prompt construction and response parsing are
separated from the actual API call (openai_client.chat_completion) so the
parsing logic can be tested with canned responses, without needing a real
OpenAI key or network access.
"""
import json
import re
from dataclasses import dataclass

from app.services import openai_client


@dataclass
class MatchScoreResult:
    score: int
    explanation: str
    matching_skills: list[str]
    missing_skills: list[str]


def _build_match_score_prompt(role_title: str, company_name: str, job_description: str, resume_text: str) -> tuple[str, str]:
    system = (
        "You are an ATS (Applicant Tracking System) analyst. Compare a candidate's resume "
        "against a job description and respond with ONLY a JSON object (no markdown, no code "
        "fences, no extra text) in this exact shape: "
        '{"score": <integer 0-100>, "explanation": "<2-3 sentence summary>", '
        '"matching_skills": ["skill1", "skill2"], "missing_skills": ["skill1", "skill2"]}'
    )
    user = (
        f"Job title: {role_title}\nCompany: {company_name}\n\n"
        f"Job description:\n{job_description}\n\n"
        f"Candidate resume:\n{resume_text}"
    )
    return system, user


def parse_match_score_response(raw_response: str) -> MatchScoreResult:
    """
    Parses the model's response into a MatchScoreResult. Models don't
    always perfectly follow "respond with only JSON" instructions (they
    sometimes wrap it in markdown code fences), so this strips common
    wrapping before parsing, and raises a clear error if it still can't
    find valid JSON rather than silently returning garbage.
    """
    cleaned = raw_response.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse AI response as JSON: {raw_response[:200]}") from e

    score = int(data.get("score", 0))
    score = max(0, min(100, score))  # clamp to a sane range regardless of what the model returned

    return MatchScoreResult(
        score=score,
        explanation=str(data.get("explanation", "")),
        matching_skills=[str(s) for s in data.get("matching_skills", [])],
        missing_skills=[str(s) for s in data.get("missing_skills", [])],
    )


async def get_match_score(role_title: str, company_name: str, job_description: str, resume_text: str) -> MatchScoreResult:
    if not job_description or not job_description.strip():
        raise ValueError("This application has no job description saved -- add one from the application detail page first.")
    if not resume_text or not resume_text.strip():
        raise ValueError("No resume text saved -- paste your resume text in Settings first.")

    system, user = _build_match_score_prompt(role_title, company_name, job_description, resume_text)
    raw = await openai_client.chat_completion(system, user, max_tokens=500)
    return parse_match_score_response(raw)


async def generate_cover_letter(role_title: str, company_name: str, job_description: str, resume_text: str, applicant_name: str) -> str:
    if not resume_text or not resume_text.strip():
        raise ValueError("No resume text saved -- paste your resume text in Settings first.")

    system = (
        "You are a professional cover letter writer. Write a concise, genuine-sounding cover "
        "letter (under 350 words) based on the candidate's resume and the job description. "
        "No placeholder brackets like [Your Name] -- use the actual name given. Avoid generic "
        "filler phrases; be specific to the role and the candidate's actual experience."
    )
    user = (
        f"Applicant name: {applicant_name}\n"
        f"Role: {role_title}\nCompany: {company_name}\n\n"
        f"Job description:\n{job_description or '(not provided)'}\n\n"
        f"Candidate resume:\n{resume_text}"
    )
    return await openai_client.chat_completion(system, user, max_tokens=600)


async def generate_follow_up_email(role_title: str, company_name: str, applied_days_ago: int, applicant_name: str, current_status: str) -> str:
    system = (
        "You are helping a job applicant write a brief, polite follow-up email to a recruiter "
        "about an application they submitted. Keep it under 120 words, professional, and not "
        "pushy. No placeholder brackets -- use the actual details given."
    )
    user = (
        f"Applicant name: {applicant_name}\n"
        f"Role: {role_title}\nCompany: {company_name}\n"
        f"Applied {applied_days_ago} days ago. Current status: {current_status}."
    )
    return await openai_client.chat_completion(system, user, max_tokens=300)
