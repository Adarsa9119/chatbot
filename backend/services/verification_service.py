"""
verification_service.py — Email verification token management.
Generates, stores, and validates email verification tokens.
Change Tracker:
  v1.0 — initial
"""

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from config.logging_config import logger
from database.crud_users import fn_get_user_by_id, fn_update_user


# ── In-memory verification token store ──────────────────────
# Structure: { token_hash: { user_id, user_email, expires_at, verified } }
# Replace with DB table (email_verifications) in production.
_verification_tokens: dict = {}

VERIFICATION_TOKEN_EXPIRE_HOURS = 24


def help_fn_hash_verify_token(token: str) -> str:
    """SHA-256 hash for safe storage."""
    return hashlib.sha256(token.encode()).hexdigest()


class VerificationService:
    """
    Manages email verification:
      1. Generate a verification token after signup
      2. Send verification email (via email_service)
      3. Verify token when user clicks the link
    """

    def fn_create_verification_token(
        self,
        user_id: int,
        user_email: str,
    ) -> str:
        """
        Create an email verification token.
        Returns the raw token (to be embedded in email link).
        """
        var_raw_token = secrets.token_urlsafe(32)
        var_token_hash = help_fn_hash_verify_token(var_raw_token)

        var_expires_at = datetime.now(timezone.utc) + timedelta(
            hours=VERIFICATION_TOKEN_EXPIRE_HOURS
        )

        _verification_tokens[var_token_hash] = {
            "user_id": user_id,
            "user_email": user_email,
            "expires_at": var_expires_at,
            "verified": False,
        }

        logger.info(
            f"Verification token created: user_id={user_id} email={user_email}"
        )
        return var_raw_token

    def fn_verify_email(self, db: Session, token: str) -> dict:
        """
        Validate verification token and mark user email as verified.
        Returns { user_id, user_email } on success.
        Raises 400 if invalid/expired/already used.
        """
        var_token_hash = help_fn_hash_verify_token(token)
        var_data = _verification_tokens.get(var_token_hash)

        if not var_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token",
            )

        if var_data["verified"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified",
            )

        if datetime.now(timezone.utc) > var_data["expires_at"]:
            del _verification_tokens[var_token_hash]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token expired — please request a new one",
            )

        # Mark as verified in store
        _verification_tokens[var_token_hash]["verified"] = True

        logger.info(
            f"Email verified: user_id={var_data['user_id']} email={var_data['user_email']}"
        )

        return {
            "user_id": var_data["user_id"],
            "user_email": var_data["user_email"],
        }

    def fn_resend_verification(
        self,
        user_id: int,
        user_email: str,
    ) -> str:
        """
        Invalidate any existing token for this user and create a new one.
        Returns the new raw token.
        """
        # Remove any previous tokens for this user
        var_to_remove = [
            k for k, v in _verification_tokens.items()
            if v["user_id"] == user_id and not v["verified"]
        ]
        for var_k in var_to_remove:
            del _verification_tokens[var_k]

        var_new_token = self.fn_create_verification_token(user_id, user_email)
        logger.info(f"Verification token resent: user_id={user_id}")
        return var_new_token

    def fn_is_verified(self, user_id: int) -> bool:
        """
        Check if user has a verified token in the store.
        NOTE: In production, store a `email_verified` boolean on the user record.
        """
        return any(
            v["user_id"] == user_id and v["verified"]
            for v in _verification_tokens.values()
        )

    def fn_cleanup_expired_tokens(self) -> int:
        """Remove expired tokens. Called by cleanup task."""
        var_now = datetime.now(timezone.utc)
        var_expired = [
            k for k, v in _verification_tokens.items()
            if v["expires_at"] < var_now
        ]
        for var_k in var_expired:
            del _verification_tokens[var_k]
        if var_expired:
            logger.info(f"Cleaned {len(var_expired)} expired verification tokens")
        return len(var_expired)


# ── Singleton ────────────────────────────────────────────────
verification_service = VerificationService()