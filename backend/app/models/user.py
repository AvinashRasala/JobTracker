import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=True)

    google_id: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)
    google_access_token_encrypted: Mapped[str] = mapped_column(String, nullable=True)
    google_refresh_token_encrypted: Mapped[str] = mapped_column(String, nullable=True)
    last_gmail_sync_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    phone_number: Mapped[str] = mapped_column(String(30), nullable=True)
    avatar_url: Mapped[str] = mapped_column(String(500), nullable=True)

    # Profile fields useful for experienced professionals; freshers can
    # simply leave these blank.
    current_ctc: Mapped[float] = mapped_column(Numeric(12, 2), nullable=True)
    current_notice_period_days: Mapped[int] = mapped_column(Integer, nullable=True)
    years_of_experience: Mapped[float] = mapped_column(Numeric(4, 1), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    applications: Mapped[list["Application"]] = relationship(back_populates="user", cascade="all, delete-orphan")
