"""
rag_service.py — Full RAG pipeline: embed → retrieve → build prompt → LLM → return.
Change Tracker:
  v1.0 — initial
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from openai import OpenAI

from config.settings import settings
from config.logging_config import logger
from database.crud_chunks import fn_search_similar_chunks
from database.crud_chat import fn_get_last_n_messages
from rag.prompt_builder import fn_build_prompt
from services.embedding_service import embedding_service


class RagService:
    """
    Orchestrates the full RAG pipeline for answering user questions.
    """

    def __init__(self):
        self._openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def fn_answer_question(
        self,
        db: Session,
        question: str,
        session_id: int,
        document_ids: Optional[List[int]] = None,
    ) -> dict:
        """
        Full RAG pipeline:
        1. Embed the question
        2. Retrieve top-K chunks from pgvector
        3. Fetch conversation history (last 6 messages)
        4. Build strict prompt
        5. Call LLM
        6. Return { answer, sources }
        """

        # ── Step 1: Embed question ───────────────────────────
        try:
            var_query_embedding = embedding_service.fn_embed_text(question)
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return {
                "answer": "I encountered an error processing your question.",
                "sources": [],
            }

        # ── Step 2: Vector search ────────────────────────────
        var_chunks = fn_search_similar_chunks(
            db=db,
            query_embedding=var_query_embedding,
            top_k=settings.TOP_K_CHUNKS,
            doc_ids=document_ids,
        )
        logger.info(f"Retrieved {len(var_chunks)} chunks for session_id={session_id}")

        # ── Step 3: Conversation history ─────────────────────
        var_history_messages = fn_get_last_n_messages(db, session_id, n=6)
        var_history = [
            {"role": msg.role, "content": msg.content}
            for msg in var_history_messages
        ]

        # ── Step 4: Build prompt ─────────────────────────────
        var_prompt = fn_build_prompt(
            context_chunks=var_chunks,
            question=question,
            history=var_history,
        )

        # ── Step 5: Call LLM ─────────────────────────────────
        try:
            var_response = self._openai_client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a secure document assistant. Answer only from provided context.",
                    },
                    {"role": "user", "content": var_prompt},
                ],
                max_tokens=settings.LLM_MAX_TOKENS,
                temperature=settings.LLM_TEMPERATURE,
            )
            var_answer = var_response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            var_answer = "I encountered an error generating a response. Please try again."

        # ── Step 6: Build sources list ───────────────────────
        var_sources = [
            {
                "chunk_id": chunk["chunk_id"],
                "doc_id": chunk["doc_id"],
                "doc_title": chunk["doc_title"],
                "chunk_text": chunk["chunk_text"],
                "page": chunk.get("metadata", {}).get("page"),
                "confidence": round(chunk.get("similarity", 0.0), 4),
            }
            for chunk in var_chunks
        ]

        return {
            "answer": var_answer,
            "sources": var_sources,
            "chunk_ids_used": [c["chunk_id"] for c in var_chunks],
        }