import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Platform(Base):
    __tablename__ = "platforms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    email_domain_pattern: Mapped[str] = mapped_column(String(255), nullable=True)
    url_pattern: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    applications: Mapped[list["Application"]] = relationship(back_populates="platform")


DEFAULT_PLATFORMS = [
    {"name": "LinkedIn Jobs", "slug": "linkedin", "email_domain_pattern": "@linkedin.com", "url_pattern": "linkedin.com/jobs"},
    {"name": "Indeed", "slug": "indeed", "email_domain_pattern": "@indeed.com", "url_pattern": "indeed.com"},
    {"name": "Naukri", "slug": "naukri", "email_domain_pattern": "@naukri.com", "url_pattern": "naukri.com"},
    {"name": "Foundit (Monster)", "slug": "foundit", "email_domain_pattern": "@foundit.in", "url_pattern": "foundit.in"},
    {"name": "Wellfound", "slug": "wellfound", "email_domain_pattern": "@wellfound.com", "url_pattern": "wellfound.com"},
    {"name": "Glassdoor", "slug": "glassdoor", "email_domain_pattern": "@glassdoor.com", "url_pattern": "glassdoor.com"},
    {"name": "Instahyre", "slug": "instahyre", "email_domain_pattern": "@instahyre.com", "url_pattern": "instahyre.com"},
    {"name": "Hirist", "slug": "hirist", "email_domain_pattern": "@hirist.com", "url_pattern": "hirist.com"},
    {"name": "Cutshort", "slug": "cutshort", "email_domain_pattern": "@cutshort.io", "url_pattern": "cutshort.io"},
    {"name": "Internshala", "slug": "internshala", "email_domain_pattern": "@internshala.com", "url_pattern": "internshala.com"},
    {"name": "Dice", "slug": "dice", "email_domain_pattern": "@dice.com", "url_pattern": "dice.com"},
    {"name": "ZipRecruiter", "slug": "ziprecruiter", "email_domain_pattern": "@ziprecruiter.com", "url_pattern": "ziprecruiter.com"},
    {"name": "Lever", "slug": "lever", "email_domain_pattern": "@lever.co", "url_pattern": "jobs.lever.co"},
    {"name": "Greenhouse", "slug": "greenhouse", "email_domain_pattern": "@greenhouse.io", "url_pattern": "boards.greenhouse.io"},
    {"name": "Workday", "slug": "workday", "email_domain_pattern": "myworkdayjobs.com", "url_pattern": "myworkdayjobs.com"},
    {"name": "SmartRecruiters", "slug": "smartrecruiters", "email_domain_pattern": "@smartrecruiters.com", "url_pattern": "smartrecruiters.com"},
    {"name": "Company Career Page", "slug": "company-site", "email_domain_pattern": None, "url_pattern": None},
    {"name": "Manual Entry", "slug": "manual", "email_domain_pattern": None, "url_pattern": None},
]
