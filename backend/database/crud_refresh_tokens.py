"""
crud_refresh_tokens.py — Database operations for refresh_tokens.
FIXED: Table was missing from original spec.
Change Tracker:
  v1.0 — initial (ADDED)
"""

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional
import hashlib
from models.refresh_token_model import RefreshTokensModel
from config.logging_config import logger


def help_fn_hash_token(token: str) -> str:
    """SHA-256 hash of the refresh token for safe storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def fn_store_refresh_token(
    db: Session,
    user_id: int,
    token: str,
    expires_at: datetime,
) -> RefreshTokensModel:
    """Store a hashed refresh token."""
    try:
        var_token_record = RefreshTokensModel(
            user_id=user_id,
            token_hash=help_fn_hash_token(token),
            expires_at=expires_at,
            revoked=False,
        )
        db.add(var_token_record)
        db.commit()
        db.refresh(var_token_record)
        return var_token_record
    except Exception as e:
        db.rollback()
        logger.error(f"fn_store_refresh_token error: {e}")
        raise


def fn_get_refresh_token(db: Session, token: str) -> Optional[RefreshTokensModel]:
    """Find a stored refresh token by its hash."""
    try:
        var_hash = help_fn_hash_token(token)
        return (
            db.query(RefreshTokensModel)
            .filter(
                RefreshTokensModel.token_hash == var_hash,
                RefreshTokensModel.revoked == False,
                RefreshTokensModel.expires_at > datetime.now(timezone.utc),
            )
            .first()
        )
    except Exception as e:
        logger.error(f"fn_get_refresh_token error: {e}")
        return None


def fn_revoke_refresh_token(db: Session, token: str) -> bool:
    """Mark a refresh token as revoked (logout)."""
    try:
        var_hash = help_fn_hash_token(token)
        var_record = db.query(RefreshTokensModel).filter(
            RefreshTokensModel.token_hash == var_hash
        ).first()
        if not var_record:
            return False
        var_record.revoked = True
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"fn_revoke_refresh_token error: {e}")
        raise


def fn_revoke_all_user_tokens(db: Session, user_id: int) -> int:
    """Revoke all refresh tokens for a user (e.g., password change)."""
    try:
        var_count = (
            db.query(RefreshTokensModel)
            .filter(RefreshTokensModel.user_id == user_id, RefreshTokensModel.revoked == False)
            .update({"revoked": True})
        )
        db.commit()
        return var_count
    except Exception as e:
        db.rollback()
        logger.error(f"fn_revoke_all_user_tokens error: {e}")
        raise