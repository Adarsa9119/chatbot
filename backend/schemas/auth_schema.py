"""
auth_schema.py — Pydantic request/response schemas for authentication.
Change Tracker:
  v1.0 — initial
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re


class LoginRequest(BaseModel):
    """POST /auth/login request body."""
    user_email: EmailStr
    user_password: str = Field(..., min_length=6)


class SignupRequest(BaseModel):
    """POST /auth/signup request body."""
    user_name: str = Field(..., min_length=3, max_length=100)
    user_role: str = Field(..., pattern="^(admin|user)$")
    user_email: EmailStr
    user_password: str = Field(..., min_length=6)
    confirm_password: str

    @field_validator("confirm_password")
    @classmethod
    def passwords_must_match(cls, v: str, info) -> str:
        if "user_password" in info.data and v != info.data["user_password"]:
            raise ValueError("Passwords do not match")
        return v


class AuthResponse(BaseModel):
    """Response after successful login or signup."""
    user_id: int
    user_name: str
    user_email: str
    user_role: str
    profile_image_url: Optional[str] = None
    message: str = "Success"

    class Config:
        from_attributes = True


class MeResponse(BaseModel):
    """GET /auth/me response."""
    user_id: int
    user_name: str
    user_email: str
    user_role: str
    profile_image_url: Optional[str] = None

    class Config:
        from_attributes = True


class LogoutResponse(BaseModel):
    """POST /auth/logout response."""
    status: str = "success"
    message: str = "Logged out successfully"