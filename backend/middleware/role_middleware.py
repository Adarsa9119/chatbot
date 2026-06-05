"""
role_middleware.py — Role-based access control (RBAC) FastAPI dependencies.
Extends auth_middleware with fine-grained permission checks.

Change Tracker:
v1.0 — initial
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from config.database import fn_get_db
from config.logging_config import logger
from middleware.auth_middleware import fn_get_current_user
from models.user_model import UsersModel


# ── Role constants ──────────────────────────────────────────────────────
ROLE_ADMIN = "admin"
ROLE_USER = "user"


def fn_require_role(required_role: str):
    """
    Factory: returns a FastAPI dependency that enforces a specific role.

    Usage:
        @router.get("/admin-only")
        def admin_route(user = Depends(fn_require_role("admin"))):
    """
    def _role_checker(
        current_user: UsersModel = Depends(fn_get_current_user),
    ) -> UsersModel:
        if current_user.user_role != required_role:
            logger.warning(
                f"Role check failed: user_id={current_user.user_id} "
                f"role={current_user.user_role} required={required_role}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access requires '{required_role}' role",
            )
        return current_user

    return _role_checker


def fn_require_admin_role(
    current_user: UsersModel = Depends(fn_get_current_user),
) -> UsersModel:
    """
    Dependency: requires admin role.
    Shorthand for fn_require_role("admin").

    Usage:
        admin = Depends(fn_require_admin_role)
    """
    if current_user.user_role != ROLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def fn_require_verified_user(
    current_user: UsersModel = Depends(fn_get_current_user),
) -> UsersModel:
    """
    Dependency: requires that the user has verified their email.
    Use this on sensitive routes to enforce email verification.

    Usage:
        user = Depends(fn_require_verified_user)
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Please verify your email to continue.",
        )
    return current_user


def fn_require_active_user(
    current_user: UsersModel = Depends(fn_get_current_user),
) -> UsersModel:
    """
    Dependency: requires user to be active (is_active flag).
    Admins can deactivate accounts without deleting them.

    Usage:
        user = Depends(fn_require_active_user)
    """
    if hasattr(current_user, "is_active") and not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact support.",
        )
    return current_user


def fn_require_self_or_admin(user_id: int):
    """
    Factory: returns a dependency that allows access if the requesting user
    is either the target user (self) OR an admin.

    Usage:
        @router.get("/users/{user_id}/profile")
        def get_profile(user_id: int, user = Depends(fn_require_self_or_admin(user_id))):
    """
    def _self_or_admin(
        current_user: UsersModel = Depends(fn_get_current_user),
    ) -> UsersModel:
        if current_user.user_id != user_id and current_user.user_role != ROLE_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: you can only access your own data",
            )
        return current_user

    return _self_or_admin