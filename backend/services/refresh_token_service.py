"""
refresh_token_service.py — Refresh token storage, rotation, and revocation.
Handles the DB-side of the refresh token lifecycle (hashed storage).
Change Tracker:
  v1.0 — initial
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, status

from config.settings import settings
from config.logging_config import logger
from database.crud_refresh_tokens import (
    fn_store_refresh_token,
    fn_get_refresh_token,
    fn_revoke_refresh_token,
    fn_revoke_all_user_tokens,
)
from database.crud_users import fn_get_user_by_id
from services.jwt_service import jwt_service


class RefreshTokenService:
    """
    Manages the full lifecycle of refresh tokens:
      - Issue (store hashed token in DB)
      - Rotate (revoke old, issue new pair)
      - Revoke (logout)
      - Revoke all (password change, security reset)
    """

    def fn_issue_token_pair(
        self,
        db: Session,
        user_id: int,
        user_name: str,
        role: str,
    ) -> dict:
        """
        Create a brand-new access + refresh token pair and persist the refresh token.
        Returns: { access_token, refresh_token, expires_at }
        Called on: login, signup, token rotation.
        """
        var_access_token = jwt_service.fn_create_access_token(user_id, user_name, role)
        var_refresh_token = jwt_service.fn_create_refresh_token(user_id)

        var_expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        fn_store_refresh_token(
            db=db,
            user_id=user_id,
            token=var_refresh_token,
            expires_at=var_expires_at,
        )

        logger.info(f"Token pair issued: user_id={user_id}")
        return {
            "access_token": var_access_token,
            "refresh_token": var_refresh_token,
            "expires_at": var_expires_at,
        }

    def fn_rotate_tokens(
        self,
        db: Session,
        old_refresh_token: str,
    ) -> dict:
        """
        Token rotation — called when the access token expires.
        1. Validate the refresh token exists and is not revoked
        2. Decode to get user_id
        3. Revoke old refresh token
        4. Issue a new token pair
        Returns: { access_token, refresh_token }
        Raises: 401 if refresh token is invalid/revoked/expired
        """
        # ── Validate token in DB (revocation check) ──────────
        var_token_record = fn_get_refresh_token(db, old_refresh_token)
        if not var_token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is invalid, expired, or revoked",
            )

        # ── Decode JWT payload ────────────────────────────────
        var_payload = jwt_service.fn_decode_refresh_token(old_refresh_token)
        if not var_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token JWT is invalid",
            )

        var_user_id: int = var_payload.get("user_id")

        # ── Fetch current user ────────────────────────────────
        var_user = fn_get_user_by_id(db, var_user_id)
        if not var_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        # ── Revoke old refresh token ──────────────────────────
        fn_revoke_refresh_token(db, old_refresh_token)

        # ── Issue new pair ────────────────────────────────────
        var_new_pair = self.fn_issue_token_pair(
            db=db,
            user_id=var_user.user_id,
            user_name=var_user.user_name,
            role=var_user.user_role,
        )

        logger.info(f"Tokens rotated: user_id={var_user_id}")
        return {
            "access_token": var_new_pair["access_token"],
            "refresh_token": var_new_pair["refresh_token"],
        }

    def fn_revoke_token(self, db: Session, refresh_token: str) -> bool:
        """
        Revoke a single refresh token (logout).
        Returns True if revoked, False if not found.
        """
        var_result = fn_revoke_refresh_token(db, refresh_token)
        if var_result:
            logger.info("Refresh token revoked (logout)")
        return var_result

    def fn_revoke_all_tokens(self, db: Session, user_id: int) -> int:
        """
        Revoke all refresh tokens for a user.
        Called on: password change, admin security reset.
        Returns count of revoked tokens.
        """
        var_count = fn_revoke_all_user_tokens(db, user_id)
        logger.info(f"All tokens revoked: user_id={user_id} count={var_count}")
        return var_count

    def fn_validate_refresh_token(
        self,
        db: Session,
        refresh_token: str,
    ) -> Optional[int]:
        """
        Validate a refresh token and return user_id.
        Returns None if invalid/expired/revoked.
        Does NOT rotate — use fn_rotate_tokens for that.
        """
        var_record = fn_get_refresh_token(db, refresh_token)
        if not var_record:
            return None
        var_payload = jwt_service.fn_decode_refresh_token(refresh_token)
        if not var_payload:
            return None
        return var_payload.get("user_id")


# ── Singleton ────────────────────────────────────────────────
refresh_token_service = RefreshTokenService()