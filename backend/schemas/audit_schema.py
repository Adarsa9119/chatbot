"""
audit_schema.py — Pydantic schemas for audit logs.
Change Tracker:
  v1.0 — initial
"""

from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class AuditLogResponse(BaseModel):
    log_id: int
    user_id: Optional[int] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    details: Optional[Any] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    total: int
    logs: List[AuditLogResponse]