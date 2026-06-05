"""
auth_middleware.py — FastAPI dependency for JWT authentication.
Change Tracker:
  v1.0 — initial
"""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Optional

from config.database import fn_get_db
from config.security import fn_decode_access_token
from config.logging_config import logger
from database.crud_users import fn_get_user_by_id
from models.user_model import UsersModel


def fn_get_current_user(
    request: Request,
    db: Session = Depends(fn_get_db),
) -> UsersModel:
    """
    FastAPI dependency — validates JWT access_token cookie.
    Returns the current user or raises 401.
    Usage: current_user: UsersModel = Depends(fn_get_current_user)
    """
    var_token = request.cookies.get("access_token")
    if not var_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated — missing access token",
        )

    var_payload = fn_decode_access_token(var_token)
    if not var_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    var_user_id: Optional[int] = var_payload.get("user_id")
    if not var_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    var_user = fn_get_user_by_id(db, var_user_id)
    if not var_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return var_user


def fn_require_admin(
    current_user: UsersModel = Depends(fn_get_current_user),
) -> UsersModel:
    """
    FastAPI dependency — requires admin role.
    Usage: admin: UsersModel = Depends(fn_require_admin)
    """
    if current_user.user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def fn_require_user(
    current_user: UsersModel = Depends(fn_get_current_user),
) -> UsersModel:
    """
    FastAPI dependency — requires any authenticated user.
    Usage: user: UsersModel = Depends(fn_require_user)
    """
    return current_user