"""
audit_controller.py — Controller for audit log retrieval (admin only).

Change Tracker:
v1.0 — initial
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from config.logging_config import logger
from database.crud_audit_logs import (
    fn_get_all_audit_logs,
    fn_get_audit_log_by_id,
    fn_get_audit_logs_by_user,
    fn_count_audit_logs,
)
from schemas.audit_schema import AuditLogResponse, AuditLogListResponse


class AuditController:
    """
    Audit log read operations (admin only):
    - fn_handle_list_logs   — paginated, filterable log list
    - fn_handle_get_log     — single log detail
    - fn_handle_user_logs   — all logs for a specific user
    """

    def fn_handle_list_logs(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        action: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> AuditLogListResponse:
        """
        GET /api/v1/audit — paginated audit log list.
        Supports filtering by action type and user_id.
        """
        var_logs = fn_get_all_audit_logs(
            db, skip=skip, limit=limit, action=action, user_id=user_id
        )
        var_total = fn_count_audit_logs(db, action=action, user_id=user_id)

        return AuditLogListResponse(
            total=var_total,
            logs=[AuditLogResponse.model_validate(log) for log in var_logs],
        )

    def fn_handle_get_log(self, db: Session, log_id: int) -> AuditLogResponse:
        """GET /api/v1/audit/{log_id} — single audit log entry."""
        var_log = fn_get_audit_log_by_id(db, log_id)
        if not var_log:
            raise HTTPException(status_code=404, detail="Audit log entry not found")
        return AuditLogResponse.model_validate(var_log)

    def fn_handle_user_logs(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> AuditLogListResponse:
        """
        GET /api/v1/audit/user/{user_id} — all audit events for a given user.
        Useful for investigating suspicious activity.
        """
        var_logs = fn_get_audit_logs_by_user(db, user_id, skip=skip, limit=limit)
        var_total = fn_count_audit_logs(db, user_id=user_id)

        return AuditLogListResponse(
            total=var_total,
            logs=[AuditLogResponse.model_validate(log) for log in var_logs],
        )


# ── Singleton ──────────────────────────────────────────────────────────
audit_controller = AuditController()