"""Symmetric encryption for secrets stored at rest (e.g. the SMTP app password).

The Fernet key is derived from ``settings.secret_key`` so there is no extra key
to manage — but it also means rotating ``SECRET_KEY`` invalidates stored
ciphertext (the secret must be re-entered). Keep ``SECRET_KEY`` stable in prod.
"""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _fernet() -> Fernet:
    # Fernet needs a 32-byte urlsafe-base64 key; derive one deterministically.
    digest = hashlib.sha256(settings.secret_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt(token: str) -> str | None:
    """Return the plaintext, or None if the token can't be decrypted (e.g. the
    secret key changed since it was written)."""
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        return None
