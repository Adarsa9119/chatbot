"""
session_service.py — Business logic for chat session lifecycle.
Handles create, rename, delete, list, and session-level analytics.
Change Tracker:
  v1.0 — initial
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status

from config.logging_config import logger
from database.crud_sessions import (
    fn_create_session,
    fn_get_session_by_id,
    fn_get_user_sessions,
    fn_rename_session,
    fn_delete_session,
    fn_count_sessions,
)
from database.crud_chat import fn_get_session_messages
from models.session_model import ChatSessionsModel


class SessionService:
    """
    Manages chat session lifecycle:
      - Create sessions
      - List sessions per user (for sidebar history)
      - Rename sessions
      - Delete sessions (cascade messages)
      - Ownership validation
    """

    def fn_create_new_session(
        self,
        db: Session,
        user_id: int,
        title: Optional[str] = None,
    ) -> ChatSessionsModel:
        """
        Create a new chat session for a user.
        Default title is 'New Chat' — auto-updated after first message.
        """
        var_session = fn_create_session(db, user_id, title or "New Chat")
        logger.info(f"Session created: id={var_session.session_id} user_id={user_id}")
        return var_session

    def fn_get_session(
        self,
        db: Session,
        session_id: int,
        user_id: int,
    ) -> ChatSessionsModel:
        """
        Fetch a session and verify it belongs to the requesting user.
        Raises 404 if not found, 403 if not owned.
        """
        var_session = fn_get_session_by_id(db, session_id)
        if not var_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        if var_session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this session",
            )
        return var_session

    def fn_list_user_sessions(
        self,
        db: Session,
        user_id: int,
    ) -> List[ChatSessionsModel]:
        """
        List all sessions for a user, ordered by most recently updated.
        Used to populate the sidebar chat history.
        """
        var_sessions = fn_get_user_sessions(db, user_id)
        logger.debug(f"Sessions listed: user_id={user_id} count={len(var_sessions)}")
        return var_sessions

    def fn_rename_session(
        self,
        db: Session,
        session_id: int,
        user_id: int,
        new_title: str,
    ) -> ChatSessionsModel:
        """Rename a session — validates ownership first."""
        self.fn_get_session(db, session_id, user_id)  # ownership check

        if not new_title or not new_title.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session title cannot be empty",
            )

        var_session = fn_rename_session(db, session_id, new_title.strip())
        logger.info(f"Session renamed: id={session_id} title='{new_title}'")
        return var_session

    def fn_delete_session(
        self,
        db: Session,
        session_id: int,
        user_id: int,
    ) -> bool:
        """Delete a session and all its messages — validates ownership."""
        self.fn_get_session(db, session_id, user_id)  # ownership check

        fn_delete_session(db, session_id)
        logger.info(f"Session deleted: id={session_id} by user_id={user_id}")
        return True

    def fn_get_session_summary(
        self,
        db: Session,
        session_id: int,
        user_id: int,
    ) -> dict:
        """
        Return a summary of a session:
        { session_id, title, message_count, created_at, updated_at }
        """
        var_session = self.fn_get_session(db, session_id, user_id)
        var_messages = fn_get_session_messages(db, session_id)

        return {
            "session_id": var_session.session_id,
            "title": var_session.title,
            "message_count": len(var_messages),
            "created_at": var_session.created_at,
            "updated_at": var_session.updated_at,
        }

    def fn_get_total_session_count(self, db: Session) -> int:
        """Admin: total session count across all users."""
        return fn_count_sessions(db)


# ── Singleton ────────────────────────────────────────────────
session_service = SessionService()