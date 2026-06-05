"""
crud_password_resets.py — All database operations for the password_resets table.
Persists password reset tokens to the DB (more durable than in-memory store).
Change Tracker:
  v1.0 — initial
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from models.password_reset_model import PasswordResetsModel
from config.logging_config import logger


# ── Token expiry ─────────────────────────────────────────────
RESET_TOKEN_EXPIRE_MINUTES = 30


# ════════════════════════════════════════════════════════════
# HASHING
# ════════════════════════════════════════════════════════════

def help_fn_hash_reset_token(raw_token: str) -> str:
    """SHA-256 hash of the raw reset token for safe DB storage."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


# ════════════════════════════════════════════════════════════
# READ
# ════════════════════════════════════════════════════════════

def fn_get_reset_token(
    db: Session,
    raw_token: str,
) -> Optional[PasswordResetsModel]:
    """
    Look up a password reset record by its SHA-256 hash.
    Returns None if:
      - Token not found
      - Token is already used (used=True)
      - Token has expired (expires_at < NOW())
    """
    try:
        var_hash = help_fn_hash_reset_token(raw_token)
        var_now = datetime.now(timezone.utc)
        return (
            db.query(PasswordResetsModel)
            .filter(
                PasswordResetsModel.token_hash == var_hash,
                PasswordResetsModel.used == False,
                PasswordResetsModel.expires_at > var_now,
            )
            .first()
        )
    except Exception as e:
        logger.error(f"fn_get_reset_token: {e}")
        return None


def fn_get_active_reset_for_user(
    db: Session,
    user_id: int,
) -> Optional[PasswordResetsModel]:
    """
    Check if a user already has an unexpired, unused reset token.
    Used before creating a new token — optionally reuse existing.
    """
    try:
        var_now = datetime.now(timezone.utc)
        return (
            db.query(PasswordResetsModel)
            .filter(
                PasswordResetsModel.user_id == user_id,
                PasswordResetsModel.used == False,
                PasswordResetsModel.expires_at > var_now,
            )
            .order_by(PasswordResetsModel.created_at.desc())
            .first()
        )
    except Exception as e:
        logger.error(f"fn_get_active_reset_for_user(user_id={user_id}): {e}")
        return None


# ════════════════════════════════════════════════════════════
# CREATE
# ════════════════════════════════════════════════════════════

def fn_create_reset_token(
    db: Session,
    user_id: int,
    ip_address: Optional[str] = None,
) -> tuple[str, PasswordResetsModel]:
    """
    Generate a cryptographically secure reset token, hash it, and store in DB.

    Process:
      1. Invalidate any existing unused tokens for this user
      2. Generate 32-byte URL-safe random token
      3. Hash with SHA-256
      4. Store hash + metadata in DB
      5. Return (raw_token, record) — raw_token is emailed to user

    Returns (raw_token: str, record: PasswordResetsModel)
    raw_token must be sent to the user — it is NOT stored in the DB.
    """
    try:
        # Invalidate previous tokens for this user
        fn_invalidate_user_reset_tokens(db, user_id)

        # Generate token
        var_raw_token = secrets.token_urlsafe(32)
        var_token_hash = help_fn_hash_reset_token(var_raw_token)
        var_expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=RESET_TOKEN_EXPIRE_MINUTES
        )

        var_record = PasswordResetsModel(
            user_id=user_id,
            token_hash=var_token_hash,
            expires_at=var_expires_at,
            used=False,
            ip_requested_from=ip_address,
        )
        db.add(var_record)
        db.commit()
        db.refresh(var_record)

        logger.info(
            f"fn_create_reset_token: reset_id={var_record.reset_id} "
            f"user_id={user_id} expires={var_expires_at}"
        )
        return var_raw_token, var_record

    except Exception as e:
        db.rollback()
        logger.error(f"fn_create_reset_token(user_id={user_id}): {e}")
        raise


# ════════════════════════════════════════════════════════════
# UPDATE
# ════════════════════════════════════════════════════════════

def fn_mark_token_used(
    db: Session,
    raw_token: str,
) -> bool:
    """
    Mark a reset token as used after successful password reset.
    Sets used=True and used_at=NOW().
    Returns True if updated, False if token not found.
    """
    try:
        var_hash = help_fn_hash_reset_token(raw_token)
        var_record = (
            db.query(PasswordResetsModel)
            .filter(PasswordResetsModel.token_hash == var_hash)
            .first()
        )
        if not var_record:
            return False

        var_record.used = True
        var_record.used_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(
            f"fn_mark_token_used: reset_id={var_record.reset_id} "
            f"user_id={var_record.user_id}"
        )
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"fn_mark_token_used: {e}")
        raise


def fn_invalidate_user_reset_tokens(db: Session, user_id: int) -> int:
    """
    Mark all unused reset tokens for a user as used (prevent reuse).
    Called before creating a new token to avoid confusion.
    Returns count of invalidated tokens.
    """
    try:
        var_count = (
            db.query(PasswordResetsModel)
            .filter(
                PasswordResetsModel.user_id == user_id,
                PasswordResetsModel.used == False,
            )
            .update(
                {"used": True, "used_at": datetime.now(timezone.utc)},
                synchronize_session=False,
            )
        )
        db.commit()
        if var_count:
            logger.info(
                f"fn_invalidate_user_reset_tokens: user_id={user_id} "
                f"invalidated={var_count}"
            )
        return var_count
    except Exception as e:
        db.rollback()
        logger.error(f"fn_invalidate_user_reset_tokens(user_id={user_id}): {e}")
        return 0


# ════════════════════════════════════════════════════════════
# CLEANUP
# ════════════════════════════════════════════════════════════

def fn_delete_expired_reset_tokens(db: Session) -> int:
    """
    Hard-delete expired AND used reset tokens.
    Called by cleanup_task.py.
    Returns count of deleted rows.
    """
    try:
        var_now = datetime.now(timezone.utc)
        var_count = (
            db.query(PasswordResetsModel)
            .filter(
                PasswordResetsModel.expires_at < var_now,
                PasswordResetsModel.used == True,
            )
            .delete(synchronize_session=False)
        )
        db.commit()
        if var_count:
            logger.info(f"fn_delete_expired_reset_tokens: deleted {var_count}")
        return var_count
    except Exception as e:
        db.rollback()
        logger.error(f"fn_delete_expired_reset_tokens: {e}")
        return 0