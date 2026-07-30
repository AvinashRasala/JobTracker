"""
Encrypts/decrypts Gmail OAuth tokens before they touch the database.
Uses Fernet (symmetric, authenticated encryption) from the `cryptography`
package, keyed by settings.ENCRYPTION_KEY.
"""
from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


def _get_fernet() -> Fernet:
    if not settings.ENCRYPTION_KEY:
        raise RuntimeError(
            "ENCRYPTION_KEY is not set. Generate one with: "
            "python3 -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\" "
            "and set it as the ENCRYPTION_KEY environment variable."
        )
    return Fernet(settings.ENCRYPTION_KEY.encode())


def encrypt_token(plain_text: str) -> str:
    return _get_fernet().encrypt(plain_text.encode()).decode()


def decrypt_token(encrypted_text: str) -> str:
    try:
        return _get_fernet().decrypt(encrypted_text.encode()).decode()
    except InvalidToken as e:
        raise ValueError("Could not decrypt stored token -- ENCRYPTION_KEY may have changed.") from e
