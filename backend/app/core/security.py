"""
Security utilities for JWT and password hashing.
"""

from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from jose import JWTError, jwt
from app.core.config import settings
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_token(
    data: dict[str, Any],
    token_type: Literal["access", "refresh"] = "access",
    expires_delta: timedelta | None = None
) -> str:
    """Create a JWT token (access or refresh).
    
    Enhanced with standard claims for better security:
    - iat (issued at timestamp)
    - jti (JWT ID for revocation)
    - iss (issuer)
    - type (custom claim for token type verification)
    """
    to_encode = data.copy()
    
    if token_type == "access":
        expire_minutes = settings.access_token_expire_minutes
    else:  # refresh token
        expire_minutes = settings.refresh_token_expire_days * 24 * 60
    
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=expire_minutes)
    
    # Add standard JWT claims
    to_encode.update({
        "exp": expire,
        "iat": now,  # Issued at timestamp
        "jti": str(uuid.uuid4()),  # JWT ID for revocation
        "iss": settings.app_name,  # Issuer
        "type": token_type  # Custom claim for token type
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt


def create_access_token(data: dict[str, Any]) -> str:
    """Create a JWT access token."""
    return create_token(data, token_type="access")


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create a JWT refresh token."""
    return create_token(data, token_type="refresh")


def decode_token(token: str) -> dict[str, Any]:
    """Decode a JWT token and return payload."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        raise


def verify_token_type(token: str, expected_type: Literal["access", "refresh"]) -> dict[str, Any]:
    """Verify token exists and has correct type."""
    payload = decode_token(token)
    token_type = payload.get("type")
    
    if token_type != expected_type:
        raise JWTError(f"Invalid token type. Expected {expected_type}, got {token_type}")
    
    return payload
