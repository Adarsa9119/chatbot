"""
crud_audit_logs.py — Database operations for audit_logs.
Change Tracker:
  v1.0 — initial
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List, Any
from models.audit_log_model import AuditLogsModel
from config.logging_config import logger


def fn_create_audit_log(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> AuditLogsModel:
    """Create an audit log entry."""
    try:
        var_log = AuditLogsModel(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
        )
        db.add(var_log)
        db.commit()
        db.refresh(var_log)
        return var_log
    except Exception as e:
        db.rollback()
        logger.error(f"fn_create_audit_log error: {e}")
        raise


def fn_get_audit_logs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
) -> List[AuditLogsModel]:
    """List audit logs with optional filters."""
    try:
        var_query = db.query(AuditLogsModel).order_by(AuditLogsModel.created_at.desc())
        if user_id:
            var_query = var_query.filter(AuditLogsModel.user_id == user_id)
        if action:
            var_query = var_query.filter(AuditLogsModel.action == action)
        return var_query.offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"fn_get_audit_logs error: {e}")
        return []


def fn_count_audit_logs(db: Session) -> int:
    """Count total audit logs."""
    try:
        return db.query(func.count(AuditLogsModel.log_id)).scalar() or 0
    except Exception as e:
        logger.error(f"fn_count_audit_logs error: {e}")
        return 0