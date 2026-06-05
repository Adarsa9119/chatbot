"""
session_schema.py — Pydantic schemas for chat session management.
Change Tracker:
  v1.0 — initial
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CreateSessionRequest(BaseModel):
    """POST /chat/sessions"""
    title: Optional[str] = Field(None, max_length=255)


class RenameSessionRequest(BaseModel):
    """PUT /chat/sessions/{id}"""
    title: str = Field(..., min_length=1, max_length=255)


class SessionResponse(BaseModel):
    """Single session record."""
    session_id: int
    user_id: int
    title: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """GET /chat/sessions response."""
    total: int
    sessions: List[SessionResponse]


class SessionDeleteResponse(BaseModel):
    status: str = "deleted"
    message: str = "Session deleted successfully"