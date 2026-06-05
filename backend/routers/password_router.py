"""
password_router.py — Password management endpoints.
Handles: forgot password, reset password, change password (authenticated).

Change Tracker:
v1.0 — initial
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from config.database import fn_get_db
from middleware.auth_middleware import fn_get_current_user
from controllers.password_controller import password_controller
from schemas.password_reset_schema import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordResponse,
    ChangePasswordResponse,
    ValidateResetTokenResponse,
)

router = APIRouter(prefix="/password", tags=["Password"])


@router.post("/forgot", response_model=ForgotPasswordResponse)
def fn_forgot_password(
    body: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(fn_get_db),
):
    """
    POST /api/v1/password/forgot — request a password reset email.

    Always returns 200 (even if email not found) to prevent user enumeration.
    Sends a reset link to the email if it exists in the system.
    Link expires in 30 minutes.
    """
    return password_controller.fn_handle_forgot_password(
        db=db,
        request=request,
        email=body.email,
    )


@router.post("/reset", response_model=ResetPasswordResponse)
def fn_reset_password(
    body: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(fn_get_db),
):
    """
    POST /api/v1/password/reset — complete password reset with token.

    Validates:
    - Token exists and has not expired
    - Token has not been used
    - Passwords match
    - New password meets minimum length (6 chars)

    On success: revokes all existing refresh tokens (forces re-login).
    """
    return password_controller.fn_handle_reset_password(
        db=db,
        request=request,
        token=body.token,
        new_password=body.new_password,
        confirm_password=body.confirm_password,
    )


@router.get("/validate-token", response_model=ValidateResetTokenResponse)
def fn_validate_reset_token(
    token: str,
):
    """
    GET /api/v1/password/validate-token?token=xxx — check token validity.

    Frontend calls this before rendering the reset form to ensure:
    - Token exists
    - Token has not expired
    - Token has not already been used

    Returns { valid: true, email: str } or raises 400.
    """
    return password_controller.fn_handle_validate_reset_token(token=token)


@router.post("/change", response_model=ChangePasswordResponse)
def fn_change_password(
    body: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(fn_get_db),
    current_user=Depends(fn_get_current_user),
):
    """
    POST /api/v1/password/change — change password for authenticated user.

    Requires:
    - Valid access token (user is logged in)
    - Current password for verification
    - New password (different from current, min 6 chars)
    - Confirm new password must match

    On success: revokes all existing refresh tokens (all devices logged out).
    """
    return password_controller.fn_handle_change_password(
        db=db,
        request=request,
        current_user=current_user,
        current_password=body.current_password,
        new_password=body.new_password,
        confirm_new_password=body.confirm_new_password,
    )