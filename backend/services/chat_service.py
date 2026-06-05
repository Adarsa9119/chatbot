"""
chat_service.py — Orchestrates the full chat ask flow.
Coordinates: session validation → RAG retrieval → LLM call → message persistence.
Change Tracker:
  v1.0 — initial
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status

from config.settings import settings
from config.logging_config import logger
from database.crud_sessions import fn_get_session_by_id, fn_rename_session
from database.crud_chat import fn_create_message, fn_get_last_n_messages
from services.vector_service import vector_service
from services.llm_service import llm_service


class ChatService:
    """
    Main service for handling a user's chat question.
    Separates the chat orchestration from the router,
    making it testable and reusable.

    Flow:
      1. Validate session ownership
      2. Vector search for relevant chunks
      3. Build conversation history
      4. LLM call with strict context
      5. Persist both user message and assistant reply
      6. Auto-title session on first message
    """

    def fn_ask(
        self,
        db: Session,
        session_id: int,
        user_id: int,
        question: str,
        document_ids: Optional[List[int]] = None,
    ) -> dict:
        """
        Process a user question end-to-end.

        Returns: {
            answer:   str,
            sources:  list of source dicts,
            chunk_ids_used: list of int,
            message_id: int (assistant message),
        }
        """

        # ── Step 1: Validate session ownership ──────────────
        var_session = fn_get_session_by_id(db, session_id)
        if not var_session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        if var_session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this session",
            )

        # ── Step 2: Vector search ────────────────────────────
        var_chunks = vector_service.fn_search(
            db=db,
            query=question,
            top_k=settings.TOP_K_CHUNKS,
            doc_ids=document_ids,
        )

        # ── Step 3: Build conversation history text ──────────
        var_history_messages = fn_get_last_n_messages(db, session_id, n=6)
        var_history_lines = []
        for var_msg in var_history_messages:
            var_role_label = "USER" if var_msg.role == "user" else "ASSISTANT"
            var_history_lines.append(f"{var_role_label}: {var_msg.content}")
        var_history_text = "\n".join(var_history_lines)

        # ── Step 4: Build context from retrieved chunks ──────
        var_context_parts = []
        for var_i, var_chunk in enumerate(var_chunks, 1):
            var_label = f"[Source {var_i}: {var_chunk.get('doc_title', 'Document')}]"
            var_context_parts.append(f"{var_label}\n{var_chunk['chunk_text']}")
        var_context = (
            "\n\n---\n\n".join(var_context_parts)
            if var_context_parts
            else "No documents available."
        )

        # ── Step 5: Call LLM ─────────────────────────────────
        var_answer = llm_service.fn_answer_from_context(
            context=var_context,
            question=question,
            history_text=var_history_text,
        )

        # ── Step 6: Persist user message ─────────────────────
        fn_create_message(
            db=db,
            session_id=session_id,
            role="user",
            content=question,
        )

        # ── Step 7: Persist assistant reply ──────────────────
        var_chunk_ids = [c["chunk_id"] for c in var_chunks]
        var_assistant_msg = fn_create_message(
            db=db,
            session_id=session_id,
            role="assistant",
            content=var_answer,
            source_chunk_ids=var_chunk_ids,
        )

        # ── Step 8: Auto-title session on first question ─────
        self.help_fn_auto_title_session(
            db=db,
            session=var_session,
            question=question,
        )

        # ── Build sources response ────────────────────────────
        var_sources = [
            {
                "chunk_id": c["chunk_id"],
                "doc_id": c["doc_id"],
                "doc_title": c["doc_title"],
                "chunk_text": c["chunk_text"],
                "page": c.get("metadata", {}).get("page"),
                "confidence": round(c.get("similarity", 0.0), 4),
            }
            for c in var_chunks
        ]

        logger.info(
            f"Chat answered: session={session_id} user={user_id} "
            f"chunks={len(var_chunks)} answer_len={len(var_answer)}"
        )

        return {
            "answer": var_answer,
            "sources": var_sources,
            "chunk_ids_used": var_chunk_ids,
            "message_id": var_assistant_msg.message_id,
        }

    def help_fn_auto_title_session(
        self,
        db: Session,
        session,
        question: str,
    ) -> None:
        """
        Auto-title a session with the first question if it still has the default title.
        Uses LLM to generate a short descriptive title (3–6 words).
        """
        try:
            if session.title in (None, "", "New Chat"):
                var_new_title = llm_service.fn_generate_session_title(question)
                fn_rename_session(db, session.session_id, var_new_title)
                logger.info(
                    f"Session auto-titled: id={session.session_id} title='{var_new_title}'"
                )
        except Exception as e:
            logger.warning(f"help_fn_auto_title_session failed (non-critical): {e}")


# ── Singleton ────────────────────────────────────────────────
chat_service = ChatService()