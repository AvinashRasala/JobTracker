import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import hash_password, verify_password, create_access_token
from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserOut,
    Token,
    UserProfileUpdate,
    PasswordChange,
    AccountReactivate,
    AccountDeleteConfirm,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

AVATAR_DIR = Path(__file__).resolve().parent.parent.parent.parent / "static" / "avatars"
ALLOWED_AVATAR_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
MAX_AVATAR_BYTES = 3 * 1024 * 1024  # 3 MB


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Use the reactivate option to sign back in.",
        )
    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)


@router.post("/reactivate", response_model=Token)
def reactivate(payload: AccountReactivate, db: Session = Depends(get_db)):
    """
    Unauthenticated on purpose -- a deactivated account has no valid way
    to get a token otherwise. Requires the same credentials as login.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    user.is_active = True
    db.commit()

    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
def update_profile(
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/avatar", response_model=UserOut)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_AVATAR_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, or WebP images are allowed")

    contents = await file.read()
    if len(contents) > MAX_AVATAR_BYTES:
        raise HTTPException(status_code=400, detail="Image must be under 3 MB")

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)

    # Remove any previous avatar file for this user before saving the new one.
    for existing in AVATAR_DIR.glob(f"{current_user.id}.*"):
        existing.unlink(missing_ok=True)

    ext = ALLOWED_AVATAR_TYPES[file.content_type]
    filename = f"{current_user.id}.{ext}"
    (AVATAR_DIR / filename).write_bytes(contents)

    current_user.avatar_url = f"/static/avatars/{filename}"
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me/avatar", response_model=UserOut)
def delete_avatar(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if AVATAR_DIR.exists():
        for existing in AVATAR_DIR.glob(f"{current_user.id}.*"):
            existing.unlink(missing_ok=True)
    current_user.avatar_url = None
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/password", status_code=204)
def change_password(
    payload: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.hashed_password or not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return None


@router.post("/me/deactivate", status_code=204)
def deactivate_account(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.is_active = False
    db.commit()
    return None


@router.post("/me/delete", status_code=204)
def delete_account(
    payload: AccountDeleteConfirm,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.hashed_password or not verify_password(payload.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Password is incorrect")

    if current_user.avatar_url and AVATAR_DIR.exists():
        for existing in AVATAR_DIR.glob(f"{current_user.id}.*"):
            existing.unlink(missing_ok=True)

    db.delete(current_user)  # cascades to applications, status_history, notes, interview_rounds
    db.commit()
    return None
