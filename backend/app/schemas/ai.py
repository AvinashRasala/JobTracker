from pydantic import BaseModel


class MatchScoreOut(BaseModel):
    score: int
    explanation: str
    matching_skills: list[str]
    missing_skills: list[str]


class CoverLetterOut(BaseModel):
    cover_letter: str


class FollowUpEmailOut(BaseModel):
    email: str
