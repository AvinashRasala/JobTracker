import enum
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DocumentType(str, enum.Enum):
    RESUME = "resume"
    COVER_LETTER = "cover_letter"
    PORTFOLIO = "portfolio"
    CERTIFICATE = "certificate"
    OTHER = "other"


class Document(Base):
    """
    Uploaded files (resume, cover letter, portfolio, certificates).
    Stored on disk under static/documents/{user_id}/ and served via the
    same StaticFiles mount used for avatars.
    """
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    document_type: Mapped[DocumentType] = mapped_column(
        SAEnum(DocumentType, name="document_type", values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        default=DocumentType.OTHER,
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g. "Resume - Backend focus"
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)  # relative path under /static
    original_filename: Mapped[str] = mapped_column(String(255), nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship()
