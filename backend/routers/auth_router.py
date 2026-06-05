"""
auth_router.py — Authentication endpoints: login, signup, logout, me, profile.
Change Tracker:
  v1.0 — initial
"""

import os
from pathlib import Path
from fastapi import APIRouter, Depends, Request, Response, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from config.database import fn_get_db
from config.settings import settings
from config.logging_config import logger
from middleware.auth_middleware import fn_get_current_user, fn_require_user
from services.auth_service import AuthService
from schemas.auth_schema import (
    LoginRequest, SignupRequest, AuthResponse, MeResponse, LogoutResponse
)
from schemas.user_schema import UserResponse


router = APIRouter(prefix="/auth", tags=["Authentication"])
var_auth_service = AuthService()

COOKIE_SETTINGS = {
    "httponly": True,
    "samesite": "lax",
    "secure": settings.APP_ENV == "production",
}


@router.post("/login", response_model=AuthResponse)
def fn_login(
    body: LoginRequest,
    response: Response,
    db: Session = Depends(fn_get_db),
):
    """POST /api/v1/auth/login — validate credentials and issue JWT cookies."""
    var_result = var_auth_service.fn_login(db, body.user_email, body.user_password)
    var_user = var_result["user"]

    response.set_cookie("access_token", var_result["access_token"], **COOKIE_SETTINGS)
    response.set_cookie("refresh_token", var_result["refresh_token"], **COOKIE_SETTINGS)

    return AuthResponse(
        user_id=var_user.user_id,
        user_name=var_user.user_name,
        user_email=var_user.user_email,
        user_role=var_user.user_role,
        profile_image_url=var_user.profile_image_url,
        message="Login successful",
    )


@router.post("/signup", response_model=AuthResponse)
def fn_signup(
    body: SignupRequest,
    response: Response,
    db: Session = Depends(fn_get_db),
):
    """POST /api/v1/auth/signup — register new user and auto-login."""
    var_result = var_auth_service.fn_signup(
        db,
        user_name=body.user_name,
        user_role=body.user_role,
        user_email=body.user_email,
        user_password=body.user_password,
    )
    var_user = var_result["user"]

    response.set_cookie("access_token", var_result["access_token"], **COOKIE_SETTINGS)
    response.set_cookie("refresh_token", var_result["refresh_token"], **COOKIE_SETTINGS)

    return AuthResponse(
        user_id=var_user.user_id,
        user_name=var_user.user_name,
        user_email=var_user.user_email,
        user_role=var_user.user_role,
        profile_image_url=var_user.profile_image_url,
        message="Account created successfully",
    )


@router.post("/logout", response_model=LogoutResponse)
def fn_logout(
    request: Request,
    response: Response,
    db: Session = Depends(fn_get_db),
):
    """POST /api/v1/auth/logout — clear cookies and revoke refresh token."""
    var_refresh_token = request.cookies.get("refresh_token")
    var_auth_service.fn_logout(db, var_refresh_token)

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return LogoutResponse()


@router.get("/me", response_model=MeResponse)
def fn_get_me(
    current_user=Depends(fn_get_current_user),
):
    """GET /api/v1/auth/me — return current user from JWT."""
    return MeResponse(
        user_id=current_user.user_id,
        user_name=current_user.user_name,
        user_email=current_user.user_email,
        user_role=current_user.user_role,
        profile_image_url=current_user.profile_image_url,
    )


@router.put("/profile", response_model=UserResponse)
async def fn_update_profile(
    user_name: Optional[str] = Form(None),
    user_email: Optional[str] = Form(None),
    user_role: Optional[str] = Form(None),
    new_password: Optional[str] = Form(None),
    confirm_new_password: Optional[str] = Form(None),
    profile_image: Optional[UploadFile] = File(None),
    current_user=Depends(fn_get_current_user),
    db: Session = Depends(fn_get_db),
):
    """PUT /api/v1/auth/profile — update profile, supports image upload."""
    # Validate password match
    if new_password and new_password != confirm_new_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    var_image_url = None
    if profile_image and profile_image.filename:
        # Validate image type
        var_allowed = {"image/jpeg", "image/png", "image/gif"}
        if profile_image.content_type not in var_allowed:
            raise HTTPException(status_code=400, detail="Profile image must be JPG, PNG, or GIF")

        # Save image using pathlib (Windows safe)
        var_img_dir = Path(settings.STATIC_DIR) / "profile_images"
        var_img_dir.mkdir(parents=True, exist_ok=True)
        var_img_filename = f"user_{current_user.user_id}_{profile_image.filename}"
        var_img_path = var_img_dir / var_img_filename

        var_contents = await profile_image.read()
        if len(var_contents) > 2 * 1024 * 1024:  # 2MB max
            raise HTTPException(status_code=400, detail="Profile image must be under 2MB")

        with open(var_img_path, "wb") as var_f:
            var_f.write(var_contents)

        var_image_url = f"/static/profile_images/{var_img_filename}"

    var_user = var_auth_service.fn_update_profile(
        db=db,
        user_id=current_user.user_id,
        current_user_role=current_user.user_role,
        user_name=user_name,
        user_email=user_email,
        user_role=user_role,
        new_password=new_password,
        profile_image_url=var_image_url,
    )

    return UserResponse.model_validate(var_user)