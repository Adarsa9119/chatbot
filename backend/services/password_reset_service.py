"""
password_reset_service.py — Secure password reset via email token.
Flow: request → send email with token → validate token → update password.
Change Tracker:
  v1.0 — initial
"""

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from config.settings import settings
from config.logging_config import logger
from config.security import fn_hash_password
from database.crud_users import fn_get_user_by_email, fn_update_user
from database.crud_refresh_tokens import fn_revoke_all_user_tokens


# ── In-memory token store ────────────────────────────────────
# Structure: { token_hash: { user_id, expires_at, used } }
# Replace with DB table (password_resets) in production.
_reset_tokens: dict = {}

RESET_TOKEN_EXPIRE_MINUTES = 30


def help_fn_hash_reset_token(token: str) -> str:
    """SHA-256 hash of the raw reset token for safe storage."""
    return hashlib.sha256(token.encode()).hexdigest()


class PasswordResetService:
    """
    Manages the password reset flow:
      1. Generate secure random token on request
      2. Send token via email (via email_service)
      3. Validate token on reset submission
      4. Update password and invalidate all sessions
    """

    def fn_create_reset_token(
        self,
        db: Session,
        user_email: str,
    ) -> tuple[str, str]:
        """
        Create a password reset token for the given email.
        Returns (raw_token, user_name) — raw_token is emailed to user.
        Raises 404 if email not registered (to prevent email enumeration,
        the router should return 200 regardless — handle there).
        """
        var_user = fn_get_user_by_email(db, user_email)
        if not var_user:
            # Silently skip — don't reveal whether email exists
            logger.info(f"Password reset requested for unknown email: {user_email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found with that email",
            )

        # Generate a cryptographically secure 32-byte token
        var_raw_token = secrets.token_urlsafe(32)
        var_token_hash = help_fn_hash_reset_token(var_raw_token)

        var_expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=RESET_TOKEN_EXPIRE_MINUTES
        )

        # Store (overwrite any previous token for this user)
        _reset_tokens[var_token_hash] = {
            "user_id": var_user.user_id,
            "user_email": user_email,
            "expires_at": var_expires_at,
            "used": False,
        }

        logger.info(
            f"Password reset token created: user_id={var_user.user_id} "
            f"expires={var_expires_at}"
        )
        return var_raw_token, var_user.user_name

    def fn_validate_reset_token(self, token: str) -> dict:
        """
        Validate a password reset token.
        Returns the stored token data dict.
        Raises 400 if token is invalid, expired, or already used.
        """
        var_token_hash = help_fn_hash_reset_token(token)
        var_data = _reset_tokens.get(var_token_hash)

        if not var_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid password reset token",
            )
        if var_data["used"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has already been used",
            )
        if datetime.now(timezone.utc) > var_data["expires_at"]:
            # Clean up expired token
            del _reset_tokens[var_token_hash]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired — please request a new one",
            )

        return var_data

    def fn_reset_password(
        self,
        db: Session,
        token: str,
        new_password: str,
    ) -> bool:
        """
        Apply a password reset:
        1. Validate token
        2. Hash new password
        3. Update user record
        4. Mark token as used
        5. Revoke all existing refresh tokens (force re-login everywhere)
        """
        var_token_hash = help_fn_hash_reset_token(token)
        var_data = self.fn_validate_reset_token(token)

        var_user_id = var_data["user_id"]
        var_hashed_pw = fn_hash_password(new_password)

        # Update password
        fn_update_user(db, var_user_id, user_password=var_hashed_pw)

        # Mark token as used
        _reset_tokens[var_token_hash]["used"] = True

        # Force logout everywhere by revoking all refresh tokens
        var_revoked = fn_revoke_all_user_tokens(db, var_user_id)

        logger.info(
            f"Password reset completed: user_id={var_user_id} "
            f"sessions_revoked={var_revoked}"
        )
        return True

    def fn_cleanup_expired_tokens(self) -> int:
        """Remove expired tokens from the in-memory store. Called by cleanup task."""
        var_now = datetime.now(timezone.utc)
        var_expired_keys = [
            k for k, v in _reset_tokens.items()
            if v["expires_at"] < var_now
        ]
        for var_k in var_expired_keys:
            del _reset_tokens[var_k]
        if var_expired_keys:
            logger.info(f"Cleaned up {len(var_expired_keys)} expired reset tokens")
        return len(var_expired_keys)


# ── Singleton ────────────────────────────────────────────────
password_reset_service = PasswordResetService()