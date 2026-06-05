"""
chat_router.py — Chat endpoints: ask, sessions, messages.
FIXED: Rate limiting on /chat/ask — 20/minute per IP.
Change Tracker:
  v1.0 — initial
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import List

from config.database import fn_get_db
from config.logging_config import logger
from middleware.auth_middleware import fn_get_current_user
from services.rag_service import RagService
from database.crud_sessions import (
    fn_create_session, fn_get_session_by_id, fn_get_user_sessions,
    fn_rename_session, fn_delete_session,
)
from database.crud_chat import fn_create_message, fn_get_session_messages
from schemas.chat_schema import (
    ChatAskRequest, ChatAskResponse, SourceChunk,
    MessageResponse, MessageListResponse,
)
from schemas.session_schema import (
    CreateSessionRequest, RenameSessionRequest,
    SessionResponse, SessionListResponse, SessionDeleteResponse,
)


# ── Rate limiter ─────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/chat", tags=["Chat"])
var_rag_service = RagService()


@router.post("/ask", response_model=ChatAskResponse)
@limiter.limit("20/minute")
def fn_chat_ask(
    request: Request,
    body: ChatAskRequest,
    db: Session = Depends(fn_get_db),
    current_user=Depends(fn_get_current_user),
):
    """
    POST /api/v1/chat/ask — RAG endpoint.
    FIXED: Rate limited to 20 requests/minute per IP.
    """
    # Verify session belongs to current user
    var_session = fn_get_session_by_id(db, body.session_id)
    if not var_session:
        raise HTTPException(status_code=404, detail="Session not found")
    if var_session.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not your session")

    # Store user message
    var_user_msg = fn_create_message(
        db=db,
        session_id=body.session_id,
        role="user",
        content=body.question,
    )

    # Run RAG pipeline
    var_result = var_rag_service.fn_answer_question(
        db=db,
        question=body.question,
        session_id=body.session_id,
        document_ids=body.document_ids,
    )

    # Store assistant message
    var_assistant_msg = fn_create_message(
        db=db,
        session_id=body.session_id,
        role="assistant",
        content=var_result["answer"],
        source_chunk_ids=var_result.get("chunk_ids_used"),
    )

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
        f"Chat answered: session={body.session_id} user={current_user.user_id} "
        f"sources={len(var_sources)}"
    )

    return ChatAskResponse(
        answer=var_result["answer"],
        sources=var_sources,
        session_id=body.session_id,
        message_id=var_assistant_msg.message_id,
    )


@router.get("/sessions", response_model=SessionListResponse)
def fn_get_sessions(
    db: Session = Depends(fn_get_db),
    current_user=Depends(fn_get_current_user),
):
    """GET /api/v1/chat/sessions — list all sessions for current user."""
    var_sessions = fn_get_user_sessions(db, current_user.user_id)
    return SessionListResponse(
        total=len(var_sessions),
        sessions=[SessionResponse.model_validate(s) for s in var_sessions],
    )


@router.post("/sessions", response_model=SessionResponse, status_code=201)
def fn_create_new_session(
    body: CreateSessionRequest,
    db: Session = Depends(fn_get_db),
    current_user=Depends(fn_get_current_user),
):
    """POST /api/v1/chat/sessions — create a new chat session."""
    var_session = fn_create_session(db, current_user.user_id, body.title or "New Chat")
    return SessionResponse.model_validate(var_session)


@router.get("/sessions/{session_id}/messages", response_model=MessageListResponse)
def fn_get_messages(
    session_id: int,
    db: Session = Depends(fn_get_db),
    current_user=Depends(fn_get_current_user),
):
    """GET /api/v1/chat/sessions/{session_id}/messages — full message history."""
    var_session = fn_get_session_by_id(db, session_id)
    if not var_session or var_session.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Session not found")

    var_messages = fn_get_session_messages(db, session_id)
    return MessageListResponse(
        session_id=session_id,
        messages=[MessageResponse.model_validate(m) for m in var_messages],
    )


@router.put("/sessions/{session_id}", response_model=SessionResponse)
def fn_rename_session_endpoint(
    session_id: int,
    body: RenameSessionRequest,
    db: Session = Depends(fn_get_db),
    current_user=Depends(fn_get_current_user),
):
    """PUT /api/v1/chat/sessions/{session_id} — rename a session."""
    var_session = fn_get_session_by_id(db, session_id)
    if not var_session or var_session.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Session not found")

    var_updated = fn_rename_session(db, session_id, body.title)
    return SessionResponse.model_validate(var_updated)


@router.delete("/sessions/{session_id}", response_model=SessionDeleteResponse)
def fn_delete_session_endpoint(
    session_id: int,
    db: Session = Depends(fn_get_db),
    current_user=Depends(fn_get_current_user),
):
    """DELETE /api/v1/chat/sessions/{session_id} — delete session and messages."""
    var_session = fn_get_session_by_id(db, session_id)
    if not var_session or var_session.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Session not found")

    fn_delete_session(db, session_id)
    return SessionDeleteResponse()