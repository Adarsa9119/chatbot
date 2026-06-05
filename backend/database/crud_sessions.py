"""
crud_sessions.py — Database operations for chat_sessions.
Change Tracker:
  v1.0 — initial
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from models.session_model import ChatSessionsModel
from config.logging_config import logger


def fn_create_session(
    db: Session,
    user_id: int,
    title: Optional[str] = "New Chat",
) -> ChatSessionsModel:
    """Create a new chat session."""
    try:
        var_session = ChatSessionsModel(user_id=user_id, title=title)
        db.add(var_session)
        db.commit()
        db.refresh(var_session)
        return var_session
    except Exception as e:
        db.rollback()
        logger.error(f"fn_create_session error: {e}")
        raise


def fn_get_session_by_id(db: Session, session_id: int) -> Optional[ChatSessionsModel]:
    """Fetch session by ID."""
    try:
        return db.query(ChatSessionsModel).filter(ChatSessionsModel.session_id == session_id).first()
    except Exception as e:
        logger.error(f"fn_get_session_by_id error: {e}")
        return None


def fn_get_user_sessions(db: Session, user_id: int) -> List[ChatSessionsModel]:
    """List all sessions for a user, ordered by most recent."""
    try:
        return (
            db.query(ChatSessionsModel)
            .filter(ChatSessionsModel.user_id == user_id)
            .order_by(ChatSessionsModel.updated_at.desc())
            .all()
        )
    except Exception as e:
        logger.error(f"fn_get_user_sessions error: {e}")
        return []


def fn_rename_session(db: Session, session_id: int, title: str) -> Optional[ChatSessionsModel]:
    """Rename a session."""
    try:
        var_session = fn_get_session_by_id(db, session_id)
        if not var_session:
            return None
        var_session.title = title
        db.commit()
        db.refresh(var_session)
        return var_session
    except Exception as e:
        db.rollback()
        logger.error(f"fn_rename_session error: {e}")
        raise


def fn_delete_session(db: Session, session_id: int) -> bool:
    """Delete a session and cascade messages."""
    try:
        var_session = fn_get_session_by_id(db, session_id)
        if not var_session:
            return False
        db.delete(var_session)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"fn_delete_session error: {e}")
        raise


def fn_count_sessions(db: Session) -> int:
    """Total session count."""
    try:
        return db.query(func.count(ChatSessionsModel.session_id)).scalar() or 0
    except Exception as e:
        logger.error(f"fn_count_sessions error: {e}")
        return 0