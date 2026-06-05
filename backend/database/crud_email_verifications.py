"""
crud_email_verifications.py — All database operations for the email_verifications table.
Change Tracker:
  v1.0 — initial
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from models.email_verification_model import EmailVerificationsModel
from config.logging_config import logger


# ── Token expiry ─────────────────────────────────────────────
VERIFICATION_TOKEN_EXPIRE_HOURS = 24


# ════════════════════════════════════════════════════════════
# HASHING
# ════════════════════════════════════════════════════════════

def help_fn_hash_verify_token(raw_token: str) -> str:
    """SHA-256 hash of the raw verification token for safe storage."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


# ════════════════════════════════════════════════════════════
# READ
# ════════════════════════════════════════════════════════════

def fn_get_verification_token(
    db: Session,
    raw_token: str,
) -> Optional[EmailVerificationsModel]:
    """
    Look up a verification record by its SHA-256 hash.
    Returns None if:
      - Token not found
      - Already verified (verified=True)
      - Token has expired (expires_at < NOW())
    """
    try:
        var_hash = help_fn_hash_verify_token(raw_token)
        var_now = datetime.now(timezone.utc)
        return (
            db.query(EmailVerificationsModel)
            .filter(
                EmailVerificationsModel.token_hash == var_hash,
                EmailVerificationsModel.verified == False,
                EmailVerificationsModel.expires_at > var_now,
            )
            .first()
        )
    except Exception as e:
        logger.error(f"fn_get_verification_token: {e}")
        return None


def fn_get_verification_by_user(
    db: Session,
    user_id: int,
) -> Optional[EmailVerificationsModel]:
    """
    Get the most recent verification record for a user.
    Used to check if a user has already verified their email.
    """
    try:
        return (
            db.query(EmailVerificationsModel)
            .filter(EmailVerificationsModel.user_id == user_id)
            .order_by(EmailVerificationsModel.created_at.desc())
            .first()
        )
    except Exception as e:
        logger.error(f"fn_get_verification_by_user(user_id={user_id}): {e}")
        return None


def fn_is_email_verified(db: Session, user_id: int) -> bool:
    """
    Check if a user's email has been verified.
    Returns True if any verification record for the user has verified=True.
    """
    try:
        return (
            db.query(EmailVerificationsModel)
            .filter(
                EmailVerificationsModel.user_id == user_id,
                EmailVerificationsModel.verified == True,
            )
            .first() is not None
        )
    except Exception as e:
        logger.error(f"fn_is_email_verified(user_id={user_id}): {e}")
        return False


# ════════════════════════════════════════════════════════════
# CREATE
# ════════════════════════════════════════════════════════════

def fn_create_verification_token(
    db: Session,
    user_id: int,
    user_email: str,
) -> tuple[str, EmailVerificationsModel]:
    """
    Generate a cryptographically secure verification token and store its hash.

    Process:
      1. Invalidate any existing unverified tokens for this user (resend case)
      2. Generate 32-byte URL-safe random token
      3. Hash with SHA-256
      4. Store hash + email snapshot + expiry in DB
      5. Return (raw_token, record)

    raw_token is embedded in the verification email link.
    raw_token is NOT stored — only its hash is in the DB.
    """
    try:
        # Invalidate old unverified tokens for this user
        fn_invalidate_user_verification_tokens(db, user_id)

        var_raw_token = secrets.token_urlsafe(32)
        var_token_hash = help_fn_hash_verify_token(var_raw_token)
        var_expires_at = datetime.now(timezone.utc) + timedelta(
            hours=VERIFICATION_TOKEN_EXPIRE_HOURS
        )

        var_record = EmailVerificationsModel(
            user_id=user_id,
            user_email=user_email.lower().strip(),
            token_hash=var_token_hash,
            expires_at=var_expires_at,
            verified=False,
        )
        db.add(var_record)
        db.commit()
        db.refresh(var_record)

        logger.info(
            f"fn_create_verification_token: verification_id={var_record.verification_id} "
            f"user_id={user_id} email={user_email}"
        )
        return var_raw_token, var_record

    except Exception as e:
        db.rollback()
        logger.error(f"fn_create_verification_token(user_id={user_id}): {e}")
        raise


# ════════════════════════════════════════════════════════════
# UPDATE
# ════════════════════════════════════════════════════════════

def fn_mark_email_verified(
    db: Session,
    raw_token: str,
) -> Optional[EmailVerificationsModel]:
    """
    Mark a verification token as verified.
    Sets verified=True and verified_at=NOW().
    Returns the updated record or None if token not found/invalid.
    """
    try:
        var_hash = help_fn_hash_verify_token(raw_token)
        var_record = (
            db.query(EmailVerificationsModel)
            .filter(EmailVerificationsModel.token_hash == var_hash)
            .first()
        )
        if not var_record:
            logger.warning("fn_mark_email_verified: token not found")
            return None

        var_record.verified = True
        var_record.verified_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(var_record)

        logger.info(
            f"fn_mark_email_verified: verification_id={var_record.verification_id} "
            f"user_id={var_record.user_id} email={var_record.user_email}"
        )
        return var_record

    except Exception as e:
        db.rollback()
        logger.error(f"fn_mark_email_verified: {e}")
        raise


def fn_invalidate_user_verification_tokens(db: Session, user_id: int) -> int:
    """
    Expire all unverified tokens for a user.
    Called before creating a new token (resend flow).
    Sets expires_at to NOW() so they fail the expiry check.
    Returns count of invalidated tokens.
    """
    try:
        var_now = datetime.now(timezone.utc)
        var_count = (
            db.query(EmailVerificationsModel)
            .filter(
                EmailVerificationsModel.user_id == user_id,
                EmailVerificationsModel.verified == False,
            )
            .update({"expires_at": var_now}, synchronize_session=False)
        )
        db.commit()
        if var_count:
            logger.info(
                f"fn_invalidate_user_verification_tokens: "
                f"user_id={user_id} invalidated={var_count}"
            )
        return var_count
    except Exception as e:
        db.rollback()
        logger.error(f"fn_invalidate_user_verification_tokens(user_id={user_id}): {e}")
        return 0


# ════════════════════════════════════════════════════════════
# COUNT
# ════════════════════════════════════════════════════════════

def fn_count_verified_users(db: Session) -> int:
    """Count users who have completed email verification."""
    try:
        return (
            db.query(func.count(func.distinct(EmailVerificationsModel.user_id)))
            .filter(EmailVerificationsModel.verified == True)
            .scalar() or 0
        )
    except Exception as e:
        logger.error(f"fn_count_verified_users: {e}")
        return 0


# ════════════════════════════════════════════════════════════
# CLEANUP
# ════════════════════════════════════════════════════════════

def fn_delete_expired_verification_tokens(db: Session) -> int:
    """
    Hard-delete expired AND verified verification tokens.
    Called by cleanup_task.py.
    Returns count of deleted rows.
    """
    try:
        var_now = datetime.now(timezone.utc)
        var_count = (
            db.query(EmailVerificationsModel)
            .filter(
                EmailVerificationsModel.expires_at < var_now,
                EmailVerificationsModel.verified == True,
            )
            .delete(synchronize_session=False)
        )
        db.commit()
        if var_count:
            logger.info(f"fn_delete_expired_verification_tokens: deleted {var_count}")
        return var_count
    except Exception as e:
        db.rollback()
        logger.error(f"fn_delete_expired_verification_tokens: {e}")
        return 0