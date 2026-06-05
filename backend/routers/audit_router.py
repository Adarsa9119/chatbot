"""
audit_router.py — Audit log endpoints (admin only).
Change Tracker:
  v1.0 — initial
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from config.database import fn_get_db
from middleware.auth_middleware import fn_require_admin
from database.crud_audit_logs import fn_get_audit_logs, fn_count_audit_logs
from schemas.audit_schema import AuditLogListResponse, AuditLogResponse


router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/logs", response_model=AuditLogListResponse)
def fn_get_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    db: Session = Depends(fn_get_db),
    admin=Depends(fn_require_admin),
):
    """GET /api/v1/audit/logs — paginated audit logs (admin only)."""
    var_logs = fn_get_audit_logs(db, skip=skip, limit=limit, user_id=user_id, action=action)
    var_total = fn_count_audit_logs(db)
    return AuditLogListResponse(
        total=var_total,
        logs=[AuditLogResponse.model_validate(log) for log in var_logs],
    )