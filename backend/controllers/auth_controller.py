"""
auth_controller.py — Controller layer for all authentication operations.
Sits between routers (HTTP) and services (business logic).
Handles: cookie management, response shaping, audit logging.
Change Tracker:
  v1.0 — initial
"""

from fastapi import HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from typing import Optional

from config.settings import settings
from config.logging_config import logger
from services.auth_service import AuthService
from services.refresh_token_service import refresh_token_service
from services.audit_service import audit_service, AuditAction
from services.email_service import email_service
from services.verification_service import verification_service
from database.crud_users import fn_get_user_by_id
from schemas.auth_schema import AuthResponse, MeResponse, LogoutResponse
from schemas.user_schema import UserResponse


# ── Cookie configuration ─────────────────────────────────────
# httponly=True → JS cannot read tokens (XSS protection)
# secure=True only in production (requires HTTPS)
COOKIE_OPTS = {
    "httponly": True,
    "samesite": "lax",
    "secure": settings.APP_ENV == "production",
}
ACCESS_COOKIE_MAX_AGE  = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
REFRESH_COOKIE_MAX_AGE = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400

_auth_service = AuthService()


class AuthController:
    """
    Handles all auth-related request logic:
      fn_handle_login          — validate credentials, set cookies
      fn_handle_signup         — register user, set cookies, send welcome email
      fn_handle_logout         — revoke refresh token, clear cookies
      fn_handle_me             — return current user from JWT
      fn_handle_profile_update — update profile fields + optional image
      fn_handle_token_refresh  — rotate access/refresh token pair
    """

    # ────────────────────────────────────────────────────────
    # Login
    # ────────────────────────────────────────────────────────

    def fn_handle_login(
        self,
        db: Session,
        request: Request,
        response: Response,
        user_email: str,
        user_password: str,
    ) -> AuthResponse:
        """
        Authenticate user and issue JWT cookies.

        Steps:
          1. Delegate credential check to auth_service
          2. Set access_token + refresh_token as HTTPonly cookies
          3. Write audit log
          4. Return AuthResponse with user data
        """
        try:
            var_result = _auth_service.fn_login(db, user_email, user_password)
        except HTTPException:
            # Log failed attempt before re-raising
            audit_service.fn_log_login_failed(db, user_email, request)
            raise

        var_user = var_result["user"]

        # ── Set HTTPonly cookies ──────────────────────────────
        self.help_fn_set_auth_cookies(
            response,
            var_result["access_token"],
            var_result["refresh_token"],
        )

        # ── Audit log ────────────────────────────────────────
        audit_service.fn_log_login(db, var_user.user_id, user_email, request)

        logger.info(
            f"Login success: user_id={var_user.user_id} role={var_user.user_role} "
            f"ip={self.help_fn_get_ip(request)}"
        )

        return AuthResponse(
            user_id=var_user.user_id,
            user_name=var_user.user_name,
            user_email=var_user.user_email,
            user_role=var_user.user_role,
            profile_image_url=var_user.profile_image_url,
            message="Login successful",
        )

    # ────────────────────────────────────────────────────────
    # Signup
    # ────────────────────────────────────────────────────────

    def fn_handle_signup(
        self,
        db: Session,
        request: Request,
        response: Response,
        user_name: str,
        user_role: str,
        user_email: str,
        user_password: str,
    ) -> AuthResponse:
        """
        Register a new user, auto-login, send welcome email.

        Steps:
          1. Create user via auth_service
          2. Set HTTPonly cookies
          3. Send welcome email (non-blocking)
          4. Create email verification token and send
          5. Write audit log
        """
        var_result = _auth_service.fn_signup(
            db,
            user_name=user_name,
            user_role=user_role,
            user_email=user_email,
            user_password=user_password,
        )
        var_user = var_result["user"]

        # ── Set cookies ──────────────────────────────────────
        self.help_fn_set_auth_cookies(
            response,
            var_result["access_token"],
            var_result["refresh_token"],
        )

        # ── Welcome email (fire-and-forget) ──────────────────
        try:
            email_service.fn_send_welcome_email(user_email, user_name)
        except Exception as e:
            logger.warning(f"Welcome email failed (non-critical): {e}")

        # ── Verification email ───────────────────────────────
        try:
            var_verify_token = verification_service.fn_create_verification_token(
                var_user.user_id, user_email
            )
            email_service.fn_send_verification_email(user_email, user_name, var_verify_token)
        except Exception as e:
            logger.warning(f"Verification email failed (non-critical): {e}")

        # ── Audit log ────────────────────────────────────────
        audit_service.fn_log_signup(db, var_user.user_id, user_email, user_role, request)

        logger.info(
            f"Signup success: user_id={var_user.user_id} role={user_role} email={user_email}"
        )

        return AuthResponse(
            user_id=var_user.user_id,
            user_name=var_user.user_name,
            user_email=var_user.user_email,
            user_role=var_user.user_role,
            profile_image_url=var_user.profile_image_url,
            message="Account created successfully",
        )

    # ────────────────────────────────────────────────────────
    # Logout
    # ────────────────────────────────────────────────────────

    def fn_handle_logout(
        self,
        db: Session,
        request: Request,
        response: Response,
        current_user_id: int,
    ) -> LogoutResponse:
        """
        Revoke refresh token, clear both cookies, log action.
        """
        var_refresh_token = request.cookies.get("refresh_token")

        # Revoke in DB (so rotation/reuse is detected)
        if var_refresh_token:
            try:
                refresh_token_service.fn_revoke_token(db, var_refresh_token)
            except Exception as e:
                logger.warning(f"Refresh token revocation error (non-critical): {e}")

        # ── Clear cookies ────────────────────────────────────
        self.help_fn_clear_auth_cookies(response)

        # ── Audit log ────────────────────────────────────────
        audit_service.fn_log_logout(db, current_user_id, request)

        logger.info(f"Logout: user_id={current_user_id}")
        return LogoutResponse()

    # ────────────────────────────────────────────────────────
    # Me
    # ────────────────────────────────────────────────────────

    def fn_handle_me(self, current_user) -> MeResponse:
        """
        Return the current authenticated user's profile from the JWT.
        No DB call needed — all data is in the JWT or in the injected user object.
        """
        return MeResponse(
            user_id=current_user.user_id,
            user_name=current_user.user_name,
            user_email=current_user.user_email,
            user_role=current_user.user_role,
            profile_image_url=current_user.profile_image_url,
        )

    # ────────────────────────────────────────────────────────
    # Profile update
    # ────────────────────────────────────────────────────────

    def fn_handle_profile_update(
        self,
        db: Session,
        request: Request,
        current_user,
        user_name: Optional[str],
        user_email: Optional[str],
        user_role: Optional[str],
        new_password: Optional[str],
        confirm_new_password: Optional[str],
        profile_image_url: Optional[str],
    ) -> UserResponse:
        """
        Update user profile.
        Validates password match before delegating to auth_service.
        Logs changed fields in audit log.
        """
        # ── Client-side validation mirror ────────────────────
        if new_password and new_password != confirm_new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New passwords do not match",
            )

        # ── Track which fields are changing for audit ────────
        var_changed_fields = []
        if user_name:
            var_changed_fields.append("user_name")
        if user_email:
            var_changed_fields.append("user_email")
        if user_role and current_user.user_role == "admin":
            var_changed_fields.append("user_role")
        if new_password:
            var_changed_fields.append("password")
        if profile_image_url:
            var_changed_fields.append("profile_image")

        # ── Delegate to service ──────────────────────────────
        var_updated_user = _auth_service.fn_update_profile(
            db=db,
            user_id=current_user.user_id,
            current_user_role=current_user.user_role,
            user_name=user_name,
            user_email=user_email,
            user_role=user_role,
            new_password=new_password,
            profile_image_url=profile_image_url,
        )

        # ── Audit ────────────────────────────────────────────
        if var_changed_fields:
            audit_service.fn_log_profile_update(
                db, current_user.user_id, var_changed_fields, request
            )

        logger.info(
            f"Profile updated: user_id={current_user.user_id} fields={var_changed_fields}"
        )

        return UserResponse.model_validate(var_updated_user)

    # ────────────────────────────────────────────────────────
    # Token refresh
    # ────────────────────────────────────────────────────────

    def fn_handle_token_refresh(
        self,
        db: Session,
        request: Request,
        response: Response,
    ) -> dict:
        """
        Rotate the token pair:
        1. Read old refresh_token from cookie
        2. Validate, revoke old, issue new pair
        3. Set new cookies
        4. Return user info
        """
        var_old_refresh = request.cookies.get("refresh_token")
        if not var_old_refresh:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No refresh token found",
            )

        var_new_tokens = refresh_token_service.fn_rotate_tokens(db, var_old_refresh)

        self.help_fn_set_auth_cookies(
            response,
            var_new_tokens["access_token"],
            var_new_tokens["refresh_token"],
        )

        logger.info("Token pair rotated successfully")
        return {"status": "tokens_refreshed"}

    # ────────────────────────────────────────────────────────
    # Cookie helpers
    # ────────────────────────────────────────────────────────

    def help_fn_set_auth_cookies(
        self,
        response: Response,
        access_token: str,
        refresh_token: str,
    ) -> None:
        """Set both JWT cookies with correct security flags."""
        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age=ACCESS_COOKIE_MAX_AGE,
            **COOKIE_OPTS,
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=REFRESH_COOKIE_MAX_AGE,
            **COOKIE_OPTS,
        )

    def help_fn_clear_auth_cookies(self, response: Response) -> None:
        """Delete both auth cookies (sets them to empty + expired)."""
        response.delete_cookie("access_token",  httponly=True, samesite="lax")
        response.delete_cookie("refresh_token", httponly=True, samesite="lax")

    def help_fn_get_ip(self, request: Request) -> str:
        """Extract client IP for logging."""
        var_forwarded = request.headers.get("X-Forwarded-For")
        if var_forwarded:
            return var_forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


# ── Singleton ────────────────────────────────────────────────
auth_controller = AuthController()