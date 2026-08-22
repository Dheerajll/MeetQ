# Security utilities for password hashing and JWT token management
# Handles password hashing (bcrypt), JWT token creation, validation, and decoding
"""
Security utilities.

Handles:
- JWT access token creation and validation (for web dashboard users)
- LMA device token generation (for local agent authentication)
"""
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

# Password hashing context (used if we ever add email/password login)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================================
# JWT — for web dashboard user sessions
# ============================================================

def create_access_token(
    subject: str,
    name: str | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        subject: The user ID or email to encode in the token.
        expires_delta: How long the token is valid.
                       Defaults to settings.access_token_expire_minutes.

    Returns:
        Encoded JWT string.
    """
    if expires_delta is None:
        expires_delta = timedelta(
            minutes=settings.access_token_expire_minutes
        )

    expire = datetime.now(timezone.utc) + expires_delta

    payload = {
        "sub": subject,
        "name": name or "",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> str | None:
    """
    Decode and validate a JWT access token.

    Args:
        token: The JWT string to decode.

    Returns:
        The subject (user ID/email) if valid, None otherwise.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ============================================================
# LMA Device Tokens — for local agent authentication
# ============================================================

def generate_lma_token() -> str:
    """
    Generate a cryptographically secure LMA device token.

    Returns:
        A 43-character URL-safe random string.
        Example: "dGhpcyBpcyBhIHZlcnkgc2VjdXJlIHRva2Vu"
    """
    return secrets.token_urlsafe(32)


# ============================================================
# Password Hashing (for future use)
# ============================================================

def hash_password(password: str) -> str:
    """Hash a plain-text password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)