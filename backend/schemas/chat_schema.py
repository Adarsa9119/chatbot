"""
chat_schema.py — Pydantic schemas for chat requests and responses.
Change Tracker:
  v1.0 — initial
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChatAskRequest(BaseModel):
    """POST /chat/ask request body."""
    question: str = Field(..., min_length=1, max_length=2000)
    document_ids: Optional[List[int]] = None  # None = search all docs
    session_id: int


class SourceChunk(BaseModel):
    """A single source chunk returned with the answer."""
    doc_id: int
    doc_title: str
    chunk_text: str
    chunk_id: int
    page: Optional[int] = None
    confidence: Optional[float] = None


class ChatAskResponse(BaseModel):
    """POST /chat/ask response."""
    answer: str
    sources: List[SourceChunk]
    session_id: int
    message_id: int


class MessageResponse(BaseModel):
    """Single chat message."""
    message_id: int
    session_id: int
    role: str
    content: str
    source_chunk_ids: Optional[List[int]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """GET /chat/sessions/{id}/messages response."""
    session_id: int
    messages: List[MessageResponse]