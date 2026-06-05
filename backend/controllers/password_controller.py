"""
password_controller.py — Controller for all password management flows.
Handles: forgot password request, reset password submission, change password.
Change Tracker:
  v1.0 — initial
"""

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from config.logging_config import logger
from services.password_reset_service import password_reset_service
from services.refresh_token_service import refresh_token_service
from services.email_service import email_service
from services.audit_service import audit_service, AuditAction
from config.security import fn_verify_password, fn_hash_password
from database.crud_users import fn_get_user_by_id, fn_update_user


# ── Response models ──────────────────────────────────────────
class ForgotPasswordResponse(BaseModel):
    status: str = "email_sent"
    message: str = "If that email is registered, a reset link has been sent"


class ResetPasswordResponse(BaseModel):
    status: str = "password_reset"
    message: str = "Password reset successfully. Please log in again."


class ChangePasswordResponse(BaseModel):
    status: str = "password_changed"
    message: str = "Password changed. All other sessions have been logged out."


class PasswordController:
    """
    Handles all password flows:
      fn_handle_forgot_password  — generate reset token + send email
      fn_handle_reset_password   — validate token + set new password
      fn_handle_change_password  — authenticated change (requires current password)
    """

    # ────────────────────────────────────────────────────────
    # Forgot password
    # ────────────────────────────────────────────────────────

    def fn_handle_forgot_password(
        self,
        db: Session,
        request: Request,
        user_email: str,
    ) -> ForgotPasswordResponse:
        """
        Step 1 of password reset: receive email, send reset link.

        Security note: ALWAYS return the same response whether the
        email exists or not — prevents email enumeration attacks.

        Steps:
          1. Try to create a reset token (silently fails if unknown email)
          2. Send reset email if token created
          3. Audit log
        """
        try:
            var_raw_token, var_user_name = password_reset_service.fn_create_reset_token(
                db, user_email
            )
            # Email is registered — send reset link
            try:
                email_service.fn_send_password_reset_email(
                    user_email, var_user_name, var_raw_token
                )
            except Exception as e:
                logger.warning(f"Reset email send failed (non-critical): {e}")

            # Audit — action happened
            audit_service.fn_log(
                db,
                action=AuditAction.PASSWORD_RESET_REQUESTED,
                details={"email": user_email},
                request=request,
            )

            logger.info(f"Password reset requested: email={user_email}")

        except HTTPException as e:
            if e.status_code == 404:
                # Unknown email — log silently, return same response
                logger.info(f"Password reset for unknown email: {user_email} (silent)")
            else:
                raise

        # Always return the same response regardless
        return ForgotPasswordResponse()

    # ────────────────────────────────────────────────────────
    # Reset password (from email link)
    # ────────────────────────────────────────────────────────

    def fn_handle_reset_password(
        self,
        db: Session,
        request: Request,
        token: str,
        new_password: str,
        confirm_password: str,
    ) -> ResetPasswordResponse:
        """
        Step 2 of password reset: validate token and update password.

        Steps:
          1. Validate passwords match (client mirror)
          2. Delegate to password_reset_service
          3. All existing refresh tokens revoked by service
          4. Audit log
        """
        # ── Client-side validation mirror ────────────────────
        if new_password != confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match",
            )
        if len(new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters",
            )

        # ── Validate token + update password ─────────────────
        # This also revokes all refresh tokens for the user
        var_token_data = password_reset_service.fn_validate_reset_token(token)
        var_user_id = var_token_data["user_id"]
        var_user_email = var_token_data["user_email"]

        password_reset_service.fn_reset_password(db, token, new_password)

        # ── Audit log ────────────────────────────────────────
        audit_service.fn_log(
            db,
            action=AuditAction.PASSWORD_RESET_COMPLETED,
            user_id=var_user_id,
            resource_type="user",
            resource_id=var_user_id,
            details={"email": var_user_email},
            request=request,
        )

        logger.info(f"Password reset completed: user_id={var_user_id}")
        return ResetPasswordResponse()

    # ────────────────────────────────────────────────────────
    # Change password (authenticated)
    # ────────────────────────────────────────────────────────

    def fn_handle_change_password(
        self,
        db: Session,
        request: Request,
        current_user,
        current_password: str,
        new_password: str,
        confirm_new_password: str,
    ) -> ChangePasswordResponse:
        """
        Authenticated password change (user knows their current password).
        Differs from reset: requires current password verification.

        Steps:
          1. Verify current password against bcrypt hash
          2. Validate new password / confirm match
          3. Update password in DB
          4. Revoke all refresh tokens (force re-login on all devices)
          5. Audit log
        """
        # ── Verify current password ──────────────────────────
        if not fn_verify_password(current_password, current_user.user_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect",
            )

        # ── Validate new password ────────────────────────────
        if new_password != confirm_new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New passwords do not match",
            )
        if len(new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 6 characters",
            )
        if new_password == current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must differ from the current password",
            )

        # ── Hash and save new password ───────────────────────
        var_new_hash = fn_hash_password(new_password)
        fn_update_user(db, current_user.user_id, user_password=var_new_hash)

        # ── Revoke all refresh tokens ────────────────────────
        var_revoked = refresh_token_service.fn_revoke_all_tokens(db, current_user.user_id)

        # ── Audit log ────────────────────────────────────────
        audit_service.fn_log(
            db,
            action=AuditAction.PASSWORD_RESET_COMPLETED,
            user_id=current_user.user_id,
            resource_type="user",
            resource_id=current_user.user_id,
            details={"method": "authenticated_change", "sessions_revoked": var_revoked},
            request=request,
        )

        logger.info(
            f"Password changed: user_id={current_user.user_id} "
            f"sessions_revoked={var_revoked}"
        )
        return ChangePasswordResponse()

    # ────────────────────────────────────────────────────────
    # Validate token (for frontend "check token before showing form")
    # ────────────────────────────────────────────────────────

    def fn_handle_validate_reset_token(self, token: str) -> dict:
        """
        GET endpoint to check if a reset token is still valid.
        Frontend calls this before rendering the reset form.
        Returns { valid: true } or raises 400.
        """
        try:
            var_data = password_reset_service.fn_validate_reset_token(token)
            return {
                "valid": True,
                "email": var_data["user_email"],
            }
        except HTTPException as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=e.detail,
            )


# ── Singleton ────────────────────────────────────────────────
password_controller = PasswordController()