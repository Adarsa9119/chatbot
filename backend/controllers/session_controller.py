"""
session_controller.py — Controller layer for chat session management.
Sits between session_router (HTTP) and session_service (business logic).

Change Tracker:
v1.0 — initial
"""

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Optional

from config.logging_config import logger
from services.session_service import session_service
from services.audit_service import audit_service, AuditAction
from schemas.session_schema import (
    SessionResponse,
    SessionListResponse,
    SessionCreateResponse,
    SessionDeleteResponse,
    SessionRenameResponse,
)


class SessionController:
    """
    Session lifecycle operations:
    - fn_handle_create_session  — new chat session
    - fn_handle_list_sessions   — all sessions for current user
    - fn_handle_get_session     — single session + summary
    - fn_handle_rename_session  — update title
    - fn_handle_delete_session  — delete session + cascade messages
    """

    def fn_handle_create_session(
        self,
        db: Session,
        request: Request,
        current_user,
        title: Optional[str] = None,
    ) -> SessionCreateResponse:
        """
        POST /api/v1/sessions — create a new chat session.
        Returns the new session object.
        """
        var_session = session_service.fn_create_new_session(
            db, user_id=current_user.user_id, title=title
        )
        audit_service.fn_log(
            db,
            action=AuditAction.SESSION_CREATED,
            user_id=current_user.user_id,
            resource_type="session",
            resource_id=var_session.session_id,
            request=request,
        )
        logger.info(
            f"Session created: id={var_session.session_id} user={current_user.user_id}"
        )
        return SessionCreateResponse(
            session_id=var_session.session_id,
            title=var_session.title,
            created_at=var_session.created_at,
            updated_at=var_session.updated_at,
        )

    def fn_handle_list_sessions(
        self,
        db: Session,
        current_user,
    ) -> SessionListResponse:
        """
        GET /api/v1/sessions — list all sessions for the current user.
        Ordered by most recently updated (for sidebar history).
        """
        var_sessions = session_service.fn_list_user_sessions(
            db, user_id=current_user.user_id
        )
        return SessionListResponse(
            total=len(var_sessions),
            sessions=[
                SessionResponse(
                    session_id=s.session_id,
                    title=s.title,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                )
                for s in var_sessions
            ],
        )

    def fn_handle_get_session(
        self,
        db: Session,
        session_id: int,
        current_user,
    ) -> dict:
        """
        GET /api/v1/sessions/{session_id} — session summary with message count.
        """
        return session_service.fn_get_session_summary(
            db, session_id=session_id, user_id=current_user.user_id
        )

    def fn_handle_rename_session(
        self,
        db: Session,
        request: Request,
        session_id: int,
        new_title: str,
        current_user,
    ) -> SessionRenameResponse:
        """
        PATCH /api/v1/sessions/{session_id} — rename a session.
        Validates ownership before updating.
        """
        var_session = session_service.fn_rename_session(
            db,
            session_id=session_id,
            user_id=current_user.user_id,
            new_title=new_title,
        )
        return SessionRenameResponse(
            session_id=var_session.session_id,
            title=var_session.title,
            updated_at=var_session.updated_at,
        )

    def fn_handle_delete_session(
        self,
        db: Session,
        request: Request,
        session_id: int,
        current_user,
    ) -> SessionDeleteResponse:
        """
        DELETE /api/v1/sessions/{session_id} — delete session + all messages.
        Validates ownership before deleting.
        """
        session_service.fn_delete_session(
            db, session_id=session_id, user_id=current_user.user_id
        )
        audit_service.fn_log(
            db,
            action=AuditAction.SESSION_DELETED,
            user_id=current_user.user_id,
            resource_type="session",
            resource_id=session_id,
            request=request,
        )
        logger.info(
            f"Session deleted: id={session_id} user={current_user.user_id}"
        )
        return SessionDeleteResponse(
            message="Session deleted successfully",
            session_id=session_id,
        )


# ── Singleton ──────────────────────────────────────────────────────────
session_controller = SessionController()