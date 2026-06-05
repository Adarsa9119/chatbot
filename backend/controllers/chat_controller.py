"""
chat_controller.py — Controller for all chat operations.
Coordinates: chat_service (RAG), session_service, audit_service.
Change Tracker:
  v1.0 — initial
"""

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List, Optional

from config.logging_config import logger
from services.chat_service import chat_service
from services.session_service import session_service
from services.audit_service import audit_service, AuditAction
from database.crud_chat import fn_get_session_messages
from schemas.chat_schema import (
    ChatAskResponse,
    SourceChunk,
    MessageResponse,
    MessageListResponse,
)
from schemas.session_schema import (
    SessionResponse,
    SessionListResponse,
    SessionDeleteResponse,
)


class ChatController:
    """
    Handles all chat-related request logic:
      fn_handle_ask               — full RAG pipeline, persist messages
      fn_handle_create_session    — new chat session
      fn_handle_list_sessions     — sidebar history
      fn_handle_get_messages      — full message thread
      fn_handle_rename_session    — rename session
      fn_handle_delete_session    — delete session + messages
    """

    # ────────────────────────────────────────────────────────
    # Ask (RAG)
    # ────────────────────────────────────────────────────────

    def fn_handle_ask(
        self,
        db: Session,
        request: Request,
        user_id: int,
        session_id: int,
        question: str,
        document_ids: Optional[List[int]],
    ) -> ChatAskResponse:
        """
        Process a user's question through the full RAG pipeline.

        Steps:
          1. Validate session ownership (in chat_service)
          2. Vector search for relevant chunks
          3. Build conversation history
          4. LLM answer generation
          5. Persist user message + assistant reply
          6. Auto-title session on first message
          7. Audit log

        Rate limiting is applied at the router level (20/min per IP).
        """
        # ── Input validation ─────────────────────────────────
        var_question = question.strip()
        if not var_question:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question cannot be empty",
            )

        # ── Delegate to chat_service (full pipeline) ─────────
        var_result = chat_service.fn_ask(
            db=db,
            session_id=session_id,
            user_id=user_id,
            question=var_question,
            document_ids=document_ids,
        )

        # ── Audit log ────────────────────────────────────────
        audit_service.fn_log_chat_sent(
            db,
            user_id=user_id,
            session_id=session_id,
            question_len=len(var_question),
        )

        # ── Shape sources for response ────────────────────────
        var_sources = [
            SourceChunk(
                chunk_id=s["chunk_id"],
                doc_id=s["doc_id"],
                doc_title=s["doc_title"],
                chunk_text=s["chunk_text"],
                page=s.get("page"),
                confidence=s.get("confidence"),
            )
            for s in var_result["sources"]
        ]

        logger.info(
            f"Chat ask: session={session_id} user={user_id} "
            f"q_len={len(var_question)} sources={len(var_sources)}"
        )

        return ChatAskResponse(
            answer=var_result["answer"],
            sources=var_sources,
            session_id=session_id,
            message_id=var_result["message_id"],
        )

    # ────────────────────────────────────────────────────────
    # Create session
    # ────────────────────────────────────────────────────────

    def fn_handle_create_session(
        self,
        db: Session,
        user_id: int,
        title: Optional[str] = None,
    ) -> SessionResponse:
        """
        Create a new chat session for the user.
        Title defaults to 'New Chat' — auto-updated after first message.
        """
        var_session = session_service.fn_create_new_session(db, user_id, title)

        # Audit
        audit_service.fn_log(
            db,
            action=AuditAction.CHAT_SESSION_CREATED,
            user_id=user_id,
            resource_type="session",
            resource_id=var_session.session_id,
        )

        logger.info(f"Session created: id={var_session.session_id} user={user_id}")
        return SessionResponse.model_validate(var_session)

    # ────────────────────────────────────────────────────────
    # List sessions (sidebar history)
    # ────────────────────────────────────────────────────────

    def fn_handle_list_sessions(
        self,
        db: Session,
        user_id: int,
    ) -> SessionListResponse:
        """
        Return all sessions for the current user, ordered by most recent.
        Used to populate the sidebar chat history panel.
        """
        var_sessions = session_service.fn_list_user_sessions(db, user_id)

        return SessionListResponse(
            total=len(var_sessions),
            sessions=[SessionResponse.model_validate(s) for s in var_sessions],
        )

    # ────────────────────────────────────────────────────────
    # Get session messages
    # ────────────────────────────────────────────────────────

    def fn_handle_get_messages(
        self,
        db: Session,
        session_id: int,
        user_id: int,
    ) -> MessageListResponse:
        """
        Return full message history for a session.
        Validates that the session belongs to the requesting user.
        """
        # Ownership check (raises 403 if not owned)
        session_service.fn_get_session(db, session_id, user_id)

        var_messages = fn_get_session_messages(db, session_id)

        return MessageListResponse(
            session_id=session_id,
            messages=[MessageResponse.model_validate(m) for m in var_messages],
        )

    # ────────────────────────────────────────────────────────
    # Rename session
    # ────────────────────────────────────────────────────────

    def fn_handle_rename_session(
        self,
        db: Session,
        session_id: int,
        user_id: int,
        new_title: str,
    ) -> SessionResponse:
        """Rename a session title. Validates ownership."""
        var_session = session_service.fn_rename_session(db, session_id, user_id, new_title)
        logger.info(f"Session renamed: id={session_id} new_title='{new_title}'")
        return SessionResponse.model_validate(var_session)

    # ────────────────────────────────────────────────────────
    # Delete session
    # ────────────────────────────────────────────────────────

    def fn_handle_delete_session(
        self,
        db: Session,
        request: Request,
        session_id: int,
        user_id: int,
    ) -> SessionDeleteResponse:
        """
        Delete a session and all its messages.
        Validates that the session belongs to the requesting user.
        """
        # Ownership check happens inside session_service
        session_service.fn_delete_session(db, session_id, user_id)

        # Audit
        audit_service.fn_log(
            db,
            action=AuditAction.CHAT_SESSION_DELETED,
            user_id=user_id,
            resource_type="session",
            resource_id=session_id,
            request=request,
        )

        logger.info(f"Session deleted: id={session_id} by user={user_id}")
        return SessionDeleteResponse()


# ── Singleton ────────────────────────────────────────────────
chat_controller = ChatController()