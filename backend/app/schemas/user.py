import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    is_admin: bool
    is_active: bool
    created_at: datetime
    phone_number: str | None = None
    avatar_url: str | None = None
    current_ctc: float | None = None
    current_notice_period_days: int | None = None
    years_of_experience: float | None = None
    resume_text: str | None = None


class UserProfileUpdate(BaseModel):
    full_name: str | None = None
    phone_number: str | None = None
    current_ctc: float | None = None
    current_notice_period_days: int | None = None
    years_of_experience: float | None = None
    resume_text: str | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class AccountReactivate(BaseModel):
    email: EmailStr
    password: str


class AccountDeleteConfirm(BaseModel):
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
