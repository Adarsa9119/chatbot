"""
admin_controller.py — Controller layer for admin-only operations.
Handles: user management, dashboard stats, document admin actions.

Change Tracker:
v1.0 — initial
"""

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Optional

from config.logging_config import logger
from services.audit_service import audit_service, AuditAction
from database.crud_users import (
    fn_get_all_users,
    fn_get_user_by_id,
    fn_update_user,
    fn_delete_user,
    fn_count_users,
)
from database.crud_documents import fn_count_documents, fn_get_all_documents
from database.crud_sessions import fn_count_sessions
from database.crud_chat import fn_count_messages
from schemas.user_schema import UserResponse, UserListResponse


class AdminController:
    """
    Admin operations:
    - fn_handle_dashboard        — aggregate stats
    - fn_handle_list_users       — paginated user list
    - fn_handle_get_user         — single user lookup
    - fn_handle_update_user_role — promote/demote
    - fn_handle_delete_user      — hard delete
    """

    # ──────────────────────────────────────────────────────────────────
    # Dashboard
    # ──────────────────────────────────────────────────────────────────

    def fn_handle_dashboard(self, db: Session) -> dict:
        """
        GET /api/v1/admin/dashboard — aggregate statistics.
        Returns counts of users, documents, sessions, messages,
        plus the 5 most recent documents.
        """
        var_total_docs = fn_count_documents(db)
        var_total_users = fn_count_users(db)
        var_total_sessions = fn_count_sessions(db)
        var_total_messages = fn_count_messages(db)
        var_recent_docs = fn_get_all_documents(db, limit=5)

        return {
            "total_documents": var_total_docs,
            "total_users": var_total_users,
            "total_sessions": var_total_sessions,
            "total_messages": var_total_messages,
            "recent_documents": [
                {
                    "doc_id": d.doc_id,
                    "title": d.title,
                    "status": d.status,
                    "created_at": d.created_at,
                }
                for d in var_recent_docs
            ],
        }

    # ──────────────────────────────────────────────────────────────────
    # User management
    # ──────────────────────────────────────────────────────────────────

    def fn_handle_list_users(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> UserListResponse:
        """GET /api/v1/admin/users — paginated list of all users."""
        var_users = fn_get_all_users(db, skip=skip, limit=limit)
        var_total = fn_count_users(db)
        return UserListResponse(
            total=var_total,
            users=[UserResponse.model_validate(u) for u in var_users],
        )

    def fn_handle_get_user(self, db: Session, user_id: int) -> UserResponse:
        """GET /api/v1/admin/users/{user_id} — single user detail."""
        var_user = fn_get_user_by_id(db, user_id)
        if not var_user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse.model_validate(var_user)

    def fn_handle_update_user_role(
        self,
        db: Session,
        request: Request,
        admin,
        user_id: int,
        new_role: str,
    ) -> UserResponse:
        """
        PATCH /api/v1/admin/users/{user_id}/role — promote/demote a user.
        Only 'user' and 'admin' roles are valid.
        """
        if new_role not in ("user", "admin"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role must be 'user' or 'admin'",
            )
        if user_id == admin.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin cannot change their own role",
            )

        var_user = fn_get_user_by_id(db, user_id)
        if not var_user:
            raise HTTPException(status_code=404, detail="User not found")

        var_old_role = var_user.user_role
        var_updated = fn_update_user(db, user_id, user_role=new_role)

        audit_service.fn_log(
            db,
            action=AuditAction.USER_ROLE_CHANGED,
            user_id=admin.user_id,
            resource_type="user",
            resource_id=user_id,
            details={"old_role": var_old_role, "new_role": new_role},
            request=request,
        )

        logger.info(
            f"Role changed: user_id={user_id} "
            f"{var_old_role} → {new_role} by admin={admin.user_id}"
        )
        return UserResponse.model_validate(var_updated)

    def fn_handle_delete_user(
        self,
        db: Session,
        request: Request,
        admin,
        user_id: int,
    ) -> dict:
        """
        DELETE /api/v1/admin/users/{user_id} — hard delete user + cascade data.
        Admin cannot delete themselves.
        """
        if user_id == admin.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin cannot delete their own account",
            )

        var_user = fn_get_user_by_id(db, user_id)
        if not var_user:
            raise HTTPException(status_code=404, detail="User not found")

        var_email = var_user.user_email
        fn_delete_user(db, user_id)

        audit_service.fn_log(
            db,
            action=AuditAction.USER_DELETED,
            user_id=admin.user_id,
            resource_type="user",
            resource_id=user_id,
            details={"deleted_email": var_email},
            request=request,
        )

        logger.info(f"User deleted: user_id={user_id} by admin={admin.user_id}")
        return {"message": "User deleted successfully", "user_id": user_id}


# ── Singleton ──────────────────────────────────────────────────────────
admin_controller = AdminController()