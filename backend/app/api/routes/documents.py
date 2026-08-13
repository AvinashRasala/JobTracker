from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.document import Document, DocumentType
from app.models.user import User
from app.schemas.document import DocumentOut

router = APIRouter(prefix="/api/documents", tags=["documents"])

DOCUMENTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "static" / "documents"
ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "image/jpeg": "jpg",
    "image/png": "png",
}
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB


@router.get("", response_model=list[DocumentOut])
def list_documents(
    document_type: DocumentType | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Document).filter(Document.user_id == current_user.id)
    if document_type:
        query = query.filter(Document.document_type == document_type)
    return query.order_by(Document.created_at.desc()).all()


@router.post("", response_model=DocumentOut, status_code=201)
async def upload_document(
    label: str = Form(...),
    document_type: DocumentType = Form(DocumentType.OTHER),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF, Word (.doc/.docx), JPEG, or PNG files are allowed")

    contents = await file.read()
    if len(contents) > MAX_FILE_BYTES:
        raise HTTPException(status_code=400, detail="File must be under 10 MB")

    user_dir = DOCUMENTS_DIR / str(current_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)

    ext = ALLOWED_TYPES[file.content_type]
    import uuid as uuid_module
    filename = f"{uuid_module.uuid4()}.{ext}"
    (user_dir / filename).write_bytes(contents)

    document = Document(
        user_id=current_user.id,
        document_type=document_type,
        label=label,
        file_path=f"/static/documents/{current_user.id}/{filename}",
        original_filename=file.filename,
        file_size=len(contents),
        mime_type=file.content_type,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = (
        db.query(Document)
        .filter(Document.id == document_id, Document.user_id == current_user.id)
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    file_on_disk = DOCUMENTS_DIR.parent.parent / document.file_path.lstrip("/")
    if file_on_disk.exists():
        file_on_disk.unlink()

    db.delete(document)
    db.commit()
    return None
