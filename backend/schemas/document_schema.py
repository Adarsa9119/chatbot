"""
document_schema.py — Pydantic schemas for document upload and retrieval.
Change Tracker:
  v1.0 — initial
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class DocumentStatusResponse(BaseModel):
    """GET /admin/documents/{doc_id}/status"""
    doc_id: int
    status: str
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Single document record."""
    doc_id: int
    title: str
    description: Optional[str] = None
    file_size_kb: Optional[int] = None
    ocr_required: bool
    status: str
    uploaded_by: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """List of documents."""
    total: int
    documents: List[DocumentResponse]


class DocumentDeleteResponse(BaseModel):
    status: str = "deleted"
    message: str = "Document deleted successfully"


class DocumentReprocessResponse(BaseModel):
    status: str = "reprocessing_started"
    doc_id: int