"""
auth_service.py — Business logic for authentication (login, signup, logout, profile).
Change Tracker:
  v1.0 — initial
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from typing import Optional

from config.security import (
    fn_hash_password, fn_verify_password,
    fn_create_access_token, fn_create_refresh_token,
)
from config.settings import settings
from config.logging_config import logger
from database.crud_users import (
    fn_get_user_by_email, fn_get_user_by_username,
    fn_create_user, fn_update_user,
)
from database.crud_refresh_tokens import fn_store_refresh_token, fn_revoke_refresh_token
from models.user_model import UsersModel


class AuthService:
    """Handles login, signup, logout, profile update logic."""

    def fn_login(
        self,
        db: Session,
        user_email: str,
        user_password: str,
    ) -> dict:
        """
        Validate credentials and issue JWT tokens.
        Returns { user, access_token, refresh_token }
        """
        var_user = fn_get_user_by_email(db, user_email)
        if not var_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not fn_verify_password(user_password, var_user.user_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        var_token_data = {
            "user_id": var_user.user_id,
            "user_name": var_user.user_name,
            "role": var_user.user_role,
        }
        var_access_token = fn_create_access_token(var_token_data)
        var_refresh_token = fn_create_refresh_token({"user_id": var_user.user_id})

        # Store refresh token in DB
        var_expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        fn_store_refresh_token(db, var_user.user_id, var_refresh_token, var_expires_at)

        logger.info(f"User logged in: id={var_user.user_id} email={user_email}")
        return {
            "user": var_user,
            "access_token": var_access_token,
            "refresh_token": var_refresh_token,
        }

    def fn_signup(
        self,
        db: Session,
        user_name: str,
        user_role: str,
        user_email: str,
        user_password: str,
    ) -> dict:
        """
        Register a new user.
        Returns { user, access_token, refresh_token }
        """
        # Check unique email
        if fn_get_user_by_email(db, user_email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        # Check unique username
        if fn_get_user_by_username(db, user_name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )

        var_hashed = fn_hash_password(user_password)
        var_user = fn_create_user(db, user_name, user_email, var_hashed, user_role)

        var_token_data = {
            "user_id": var_user.user_id,
            "user_name": var_user.user_name,
            "role": var_user.user_role,
        }
        var_access_token = fn_create_access_token(var_token_data)
        var_refresh_token = fn_create_refresh_token({"user_id": var_user.user_id})

        var_expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        fn_store_refresh_token(db, var_user.user_id, var_refresh_token, var_expires_at)

        logger.info(f"New user signed up: id={var_user.user_id} email={user_email} role={user_role}")
        return {
            "user": var_user,
            "access_token": var_access_token,
            "refresh_token": var_refresh_token,
        }

    def fn_logout(self, db: Session, refresh_token: Optional[str]) -> bool:
        """Revoke refresh token on logout."""
        if refresh_token:
            fn_revoke_refresh_token(db, refresh_token)
        return True

    def fn_update_profile(
        self,
        db: Session,
        user_id: int,
        current_user_role: str,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        user_role: Optional[str] = None,
        new_password: Optional[str] = None,
        profile_image_url: Optional[str] = None,
    ) -> UsersModel:
        """
        Update user profile.
        Role change only allowed if current user is admin.
        """
        var_updates: dict = {}

        if user_name:
            var_updates["user_name"] = user_name
        if user_email:
            # Check email not taken by another user
            var_existing = fn_get_user_by_email(db, user_email)
            if var_existing and var_existing.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already in use",
                )
            var_updates["user_email"] = user_email
        if user_role and current_user_role == "admin":
            var_updates["user_role"] = user_role
        if new_password:
            var_updates["user_password"] = fn_hash_password(new_password)
        if profile_image_url:
            var_updates["profile_image_url"] = profile_image_url

        var_user = fn_update_user(db, user_id, **var_updates)
        if not var_user:
            raise HTTPException(status_code=404, detail="User not found")

        return var_user