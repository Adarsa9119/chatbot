"""
audit_service.py — Structured audit logging for all significant system actions.
Wraps crud_audit_logs with typed action constants and helper methods.
Change Tracker:
  v1.0 — initial
"""

from sqlalchemy.orm import Session
from typing import Optional, List
from fastapi import Request

from config.logging_config import logger
from database.crud_audit_logs import fn_create_audit_log, fn_get_audit_logs, fn_count_audit_logs
from models.audit_log_model import AuditLogsModel


# ── Audit action constants ───────────────────────────────────
# Use these constants everywhere to ensure consistent action names in the DB.
class AuditAction:
    # Auth
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_SIGNUP = "user_signup"
    USER_LOGIN_FAILED = "user_login_failed"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"
    EMAIL_VERIFIED = "email_verified"
    PROFILE_UPDATED = "profile_updated"

    # Documents
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_DELETE = "document_delete"
    DOCUMENT_REPROCESS = "document_reprocess"
    DOCUMENT_PROCESSED = "document_processed"
    DOCUMENT_FAILED = "document_failed"

    # Chat
    CHAT_SESSION_CREATED = "chat_session_created"
    CHAT_SESSION_DELETED = "chat_session_deleted"
    CHAT_MESSAGE_SENT = "chat_message_sent"

    # Admin
    USER_DELETED_BY_ADMIN = "user_deleted_by_admin"
    USER_ROLE_CHANGED = "user_role_changed"


class AuditService:
    """
    Centralized audit logging service.
    All significant user/admin actions should go through this service.

    Usage:
        audit_service.fn_log(
            db, action=AuditAction.USER_LOGIN,
            user_id=1, resource_type='user', resource_id=1,
            details={'email': 'a@b.com'}, request=request
        )
    """

    def fn_log(
        self,
        db: Session,
        action: str,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        details: Optional[dict] = None,
        request: Optional[Request] = None,
        ip_address: Optional[str] = None,
    ) -> Optional[AuditLogsModel]:
        """
        Create an audit log entry.
        Never raises — audit failure must not break the main request flow.

        Args:
            action:        one of the AuditAction constants
            user_id:       the user who performed the action
            resource_type: 'document', 'user', 'session', etc.
            resource_id:   ID of the affected resource
            details:       arbitrary dict of extra info (stored as JSONB)
            request:       FastAPI Request object — used to extract IP
            ip_address:    explicit IP if request not available
        """
        try:
            var_ip = ip_address
            if not var_ip and request:
                var_ip = self.help_fn_get_client_ip(request)

            var_log = fn_create_audit_log(
                db=db,
                action=action,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
                ip_address=var_ip,
            )
            logger.debug(
                f"Audit log: action={action} user={user_id} "
                f"resource={resource_type}:{resource_id}"
            )
            return var_log

        except Exception as e:
            # Never let audit logging break the main flow
            logger.error(f"fn_log (audit) failed — non-critical: {e}")
            return None

    # ── Convenience wrappers ─────────────────────────────────

    def fn_log_login(
        self, db: Session, user_id: int, user_email: str, request: Optional[Request] = None
    ) -> None:
        self.fn_log(
            db, action=AuditAction.USER_LOGIN,
            user_id=user_id, resource_type="user", resource_id=user_id,
            details={"email": user_email}, request=request,
        )

    def fn_log_login_failed(
        self, db: Session, user_email: str, request: Optional[Request] = None
    ) -> None:
        self.fn_log(
            db, action=AuditAction.USER_LOGIN_FAILED,
            details={"email": user_email}, request=request,
        )

    def fn_log_logout(
        self, db: Session, user_id: int, request: Optional[Request] = None
    ) -> None:
        self.fn_log(
            db, action=AuditAction.USER_LOGOUT,
            user_id=user_id, resource_type="user", resource_id=user_id,
            request=request,
        )

    def fn_log_signup(
        self, db: Session, user_id: int, user_email: str, role: str, request: Optional[Request] = None
    ) -> None:
        self.fn_log(
            db, action=AuditAction.USER_SIGNUP,
            user_id=user_id, resource_type="user", resource_id=user_id,
            details={"email": user_email, "role": role}, request=request,
        )

    def fn_log_document_upload(
        self, db: Session, user_id: int, doc_id: int, doc_title: str, request: Optional[Request] = None
    ) -> None:
        self.fn_log(
            db, action=AuditAction.DOCUMENT_UPLOAD,
            user_id=user_id, resource_type="document", resource_id=doc_id,
            details={"title": doc_title}, request=request,
        )

    def fn_log_document_delete(
        self, db: Session, user_id: int, doc_id: int, request: Optional[Request] = None
    ) -> None:
        self.fn_log(
            db, action=AuditAction.DOCUMENT_DELETE,
            user_id=user_id, resource_type="document", resource_id=doc_id,
            request=request,
        )

    def fn_log_chat_sent(
        self, db: Session, user_id: int, session_id: int, question_len: int
    ) -> None:
        self.fn_log(
            db, action=AuditAction.CHAT_MESSAGE_SENT,
            user_id=user_id, resource_type="session", resource_id=session_id,
            details={"question_length": question_len},
        )

    def fn_log_profile_update(
        self, db: Session, user_id: int, fields_changed: List[str], request: Optional[Request] = None
    ) -> None:
        self.fn_log(
            db, action=AuditAction.PROFILE_UPDATED,
            user_id=user_id, resource_type="user", resource_id=user_id,
            details={"fields_changed": fields_changed}, request=request,
        )

    # ── Query helpers ────────────────────────────────────────

    def fn_get_logs(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
    ) -> List[AuditLogsModel]:
        """Fetch audit logs with optional filters."""
        return fn_get_audit_logs(db, skip=skip, limit=limit, user_id=user_id, action=action)

    def fn_count_logs(self, db: Session) -> int:
        """Total audit log count."""
        return fn_count_audit_logs(db)

    # ── IP extraction ────────────────────────────────────────

    def help_fn_get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, handling reverse proxies."""
        var_forwarded = request.headers.get("X-Forwarded-For")
        if var_forwarded:
            return var_forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"


# ── Singleton ────────────────────────────────────────────────
audit_service = AuditService()