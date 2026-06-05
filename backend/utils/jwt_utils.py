"""
jwt_utils.py — JWT creation and decoding helpers.

All JWT logic lives here so routers / services stay thin.
The config.security module may delegate to these functions or call them directly.

Change Tracker:
    v1.0 — initial
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from config.settings import settings
from config.logging_config import logger


# ── Token type constants ──────────────────────────────────────────────────────

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def fn_create_access_token(
    subject: str | int,
    extra_claims: Optional[dict] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject:       The token subject (typically user_id as string).
        extra_claims:  Additional claims to embed (e.g. {'role': 'admin'}).
        expires_delta: Custom expiry; defaults to settings.ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Signed JWT string.
    """
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    payload: dict = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "type": TOKEN_TYPE_ACCESS,
    }
    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    logger.debug(f"Access token created for sub={subject}, exp={expire}")
    return token


def fn_create_refresh_token(
    subject: str | int,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT refresh token.

    Refresh tokens carry only 'sub', 'iat', 'exp', and 'type'.

    Args:
        subject:       The token subject (typically user_id as string).
        expires_delta: Custom expiry; defaults to settings.REFRESH_TOKEN_EXPIRE_DAYS.

    Returns:
        Signed JWT string.
    """
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    payload: dict = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "type": TOKEN_TYPE_REFRESH,
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    logger.debug(f"Refresh token created for sub={subject}, exp={expire}")
    return token


def fn_decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.

    Args:
        token: The raw JWT string.

    Returns:
        Decoded payload dict on success.

    Raises:
        JWTError: If the token is expired, invalid, or wrong type.
    """
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    if payload.get("type") != TOKEN_TYPE_ACCESS:
        raise JWTError("Token type mismatch — expected access token.")
    return payload


def fn_decode_refresh_token(token: str) -> dict:
    """
    Decode and validate a JWT refresh token.

    Args:
        token: The raw JWT string.

    Returns:
        Decoded payload dict on success.

    Raises:
        JWTError: If the token is expired, invalid, or wrong type.
    """
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    if payload.get("type") != TOKEN_TYPE_REFRESH:
        raise JWTError("Token type mismatch — expected refresh token.")
    return payload