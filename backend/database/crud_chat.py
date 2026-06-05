"""
crud_chat.py — Database operations for chat_messages.
Change Tracker:
  v1.0 — initial
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from models.chat_model import ChatMessagesModel
from config.logging_config import logger


def fn_create_message(
    db: Session,
    session_id: int,
    role: str,
    content: str,
    source_chunk_ids: Optional[List[int]] = None,
) -> ChatMessagesModel:
    """Insert a chat message into a session."""
    try:
        var_message = ChatMessagesModel(
            session_id=session_id,
            role=role,
            content=content,
            source_chunk_ids=source_chunk_ids,
        )
        db.add(var_message)
        db.commit()
        db.refresh(var_message)
        return var_message
    except Exception as e:
        db.rollback()
        logger.error(f"fn_create_message error: {e}")
        raise


def fn_get_session_messages(
    db: Session,
    session_id: int,
    limit: Optional[int] = None,
) -> List[ChatMessagesModel]:
    """Fetch all messages for a session, ordered by creation time."""
    try:
        var_query = (
            db.query(ChatMessagesModel)
            .filter(ChatMessagesModel.session_id == session_id)
            .order_by(ChatMessagesModel.created_at.asc())
        )
        if limit:
            var_query = var_query.limit(limit)
        return var_query.all()
    except Exception as e:
        logger.error(f"fn_get_session_messages error: {e}")
        return []


def fn_get_last_n_messages(db: Session, session_id: int, n: int = 6) -> List[ChatMessagesModel]:
    """
    Fetch the last N messages for conversation history.
    FIXED: Required for multi-turn RAG — LLM needs conversation context.
    """
    try:
        var_messages = (
            db.query(ChatMessagesModel)
            .filter(ChatMessagesModel.session_id == session_id)
            .order_by(ChatMessagesModel.created_at.desc())
            .limit(n)
            .all()
        )
        return list(reversed(var_messages))
    except Exception as e:
        logger.error(f"fn_get_last_n_messages error: {e}")
        return []


def fn_count_messages(db: Session) -> int:
    """Total message count across all sessions."""
    try:
        return db.query(func.count(ChatMessagesModel.message_id)).scalar() or 0
    except Exception as e:
        logger.error(f"fn_count_messages error: {e}")
        return 0