import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.document import DocumentType


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_type: DocumentType
    label: str
    file_path: str
    original_filename: str | None
    file_size: int | None
    mime_type: str | None
    created_at: datetime
