"""
user_schema.py — Pydantic schemas for user profile operations.
Change Tracker:
  v1.0 — initial
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UpdateProfileRequest(BaseModel):
    """PUT /auth/profile — fields are all optional."""
    user_name: Optional[str] = Field(None, min_length=3, max_length=100)
    user_email: Optional[EmailStr] = None
    user_role: Optional[str] = Field(None, pattern="^(admin|user)$")
    new_password: Optional[str] = Field(None, min_length=6)
    confirm_new_password: Optional[str] = None


class UserResponse(BaseModel):
    """Full user record — returned in admin user list."""
    user_id: int
    user_name: str
    user_email: str
    user_role: str
    profile_image_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Admin: paginated list of users."""
    total: int
    users: list[UserResponse]