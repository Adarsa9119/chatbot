"""
jwt_service.py — JWT token creation, validation, rotation, and blacklisting.
Centralises all JWT logic so no router/service imports jose directly.
Change Tracker:
  v1.0 — initial
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status

from config.settings import settings
from config.logging_config import logger


# ── In-memory blacklist (restart clears it; use Redis in production) ──
# Stores jti (token ID) of invalidated tokens until they expire.
_token_blacklist: set[str] = set()


class JwtService:
    """
    Handles all JWT operations:
      - Create access/refresh tokens
      - Decode and validate tokens
      - Blacklist tokens (immediate logout)
      - Rotate access tokens from refresh token
    """

    # ────────────────────────────────────────────────────────
    # Creation
    # ────────────────────────────────────────────────────────

    def fn_create_access_token(
        self,
        user_id: int,
        user_name: str,
        role: str,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a signed JWT access token.
        Payload includes: user_id, user_name, role, type, exp, iat.
        """
        var_now = datetime.now(timezone.utc)
        var_expire = var_now + (
            expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        var_payload = {
            "user_id": user_id,
            "user_name": user_name,
            "role": role,
            "type": "access",
            "iat": int(var_now.timestamp()),
            "exp": var_expire,
        }
        var_token = jwt.encode(
            var_payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        logger.debug(f"Access token created for user_id={user_id} expires={var_expire}")
        return var_token

    def fn_create_refresh_token(
        self,
        user_id: int,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a signed JWT refresh token.
        Payload includes: user_id, type, exp, iat.
        """
        var_now = datetime.now(timezone.utc)
        var_expire = var_now + (
            expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        var_payload = {
            "user_id": user_id,
            "type": "refresh",
            "iat": int(var_now.timestamp()),
            "exp": var_expire,
        }
        var_token = jwt.encode(
            var_payload,
            settings.JWT_REFRESH_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )
        logger.debug(f"Refresh token created for user_id={user_id} expires={var_expire}")
        return var_token

    # ────────────────────────────────────────────────────────
    # Decoding
    # ────────────────────────────────────────────────────────

    def fn_decode_access_token(self, token: str) -> Optional[dict]:
        """
        Decode and validate an access token.
        Returns payload dict or None if invalid/expired/blacklisted.
        """
        try:
            var_payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            if var_payload.get("type") != "access":
                logger.warning("Token type mismatch — expected 'access'")
                return None
            # Check blacklist
            var_jti = var_payload.get("jti")
            if var_jti and var_jti in _token_blacklist:
                logger.warning(f"Blacklisted token used: jti={var_jti}")
                return None
            return var_payload
        except JWTError as e:
            logger.warning(f"fn_decode_access_token failed: {e}")
            return None

    def fn_decode_refresh_token(self, token: str) -> Optional[dict]:
        """
        Decode and validate a refresh token.
        Returns payload dict or None if invalid/expired.
        """
        try:
            var_payload = jwt.decode(
                token,
                settings.JWT_REFRESH_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
            )
            if var_payload.get("type") != "refresh":
                logger.warning("Token type mismatch — expected 'refresh'")
                return None
            return var_payload
        except JWTError as e:
            logger.warning(f"fn_decode_refresh_token failed: {e}")
            return None

    # ────────────────────────────────────────────────────────
    # Validation helpers
    # ────────────────────────────────────────────────────────

    def fn_validate_access_token_or_raise(self, token: str) -> dict:
        """
        Same as fn_decode_access_token but raises HTTPException on failure.
        Used in middleware where we must abort the request.
        """
        var_payload = self.fn_decode_access_token(token)
        if not var_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token",
            )
        return var_payload

    def fn_get_user_id_from_token(self, token: str) -> Optional[int]:
        """Extract user_id from access token without raising."""
        var_payload = self.fn_decode_access_token(token)
        if var_payload:
            return var_payload.get("user_id")
        return None

    def fn_get_role_from_token(self, token: str) -> Optional[str]:
        """Extract role from access token without raising."""
        var_payload = self.fn_decode_access_token(token)
        if var_payload:
            return var_payload.get("role")
        return None

    def fn_is_token_expired(self, token: str, is_refresh: bool = False) -> bool:
        """Check if a token is expired (without raising)."""
        try:
            var_secret = settings.JWT_REFRESH_SECRET if is_refresh else settings.JWT_SECRET_KEY
            jwt.decode(token, var_secret, algorithms=[settings.JWT_ALGORITHM])
            return False
        except JWTError:
            return True

    # ────────────────────────────────────────────────────────
    # Blacklisting
    # ────────────────────────────────────────────────────────

    def fn_blacklist_token(self, token: str) -> None:
        """
        Add a token's jti to the in-memory blacklist.
        Used for immediate logout invalidation.
        NOTE: Blacklist is in-memory — does not survive server restart.
              For production, replace with Redis SET with TTL.
        """
        try:
            var_payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_exp": False},
            )
            var_jti = var_payload.get("jti")
            if var_jti:
                _token_blacklist.add(var_jti)
                logger.info(f"Token blacklisted: jti={var_jti}")
        except JWTError as e:
            logger.warning(f"fn_blacklist_token failed: {e}")

    # ────────────────────────────────────────────────────────
    # Token expiry info
    # ────────────────────────────────────────────────────────

    def fn_get_access_token_expiry(self) -> datetime:
        """Return the expiry datetime for a new access token (for cookie maxAge)."""
        return datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    def fn_get_refresh_token_expiry(self) -> datetime:
        """Return the expiry datetime for a new refresh token."""
        return datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )


# ── Singleton ────────────────────────────────────────────────
jwt_service = JwtService()