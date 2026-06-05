"""
retrieval.py — Vector similarity search using pgvector.
Retrieves the most relevant document chunks for a given query embedding.

Change Tracker:
v1.0 — initial
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from config.settings import settings
from config.logging_config import logger
from models.chunk_model import ChunksModel
from models.document_model import DocumentsModel
from services.embedding_service import embedding_service


def fn_search_similar_chunks(
    db: Session,
    query_embedding: List[float],
    top_k: int = None,
    doc_ids: Optional[List[int]] = None,
    min_similarity: float = 0.0,
) -> List[dict]:
    """
    Vector similarity search using pgvector cosine distance.

    Args:
        db:               SQLAlchemy session.
        query_embedding:  Query vector (384 dims from EmbeddingService).
        top_k:            How many chunks to return. Defaults to settings.TOP_K_CHUNKS.
        doc_ids:          Optional list of document IDs to restrict search.
                          If None or empty, searches across ALL ready documents.
        min_similarity:   Minimum cosine similarity threshold (0.0–1.0).
                          Chunks below this threshold are excluded.

    Returns:
        List of chunk dicts sorted by similarity (descending):
        [
            {
                "chunk_id":   int,
                "doc_id":     int,
                "doc_title":  str,
                "chunk_text": str,
                "chunk_index": int,
                "similarity": float,
                "metadata":   dict | None,
            },
            ...
        ]
    """
    var_top_k = top_k or settings.TOP_K_CHUNKS
    var_embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

    try:
        # ── Build base query ───────────────────────────────────────────
        var_query = (
            db.query(
                ChunksModel,
                DocumentsModel.title.label("doc_title"),
                (
                    1 - ChunksModel.embedding.cosine_distance(query_embedding)
                ).label("similarity"),
            )
            .join(DocumentsModel, ChunksModel.doc_id == DocumentsModel.doc_id)
            .filter(DocumentsModel.status == "ready")
            .filter(ChunksModel.embedding.is_not(None))
        )

        # ── Filter by document IDs if provided ─────────────────────────
        if doc_ids:
            var_query = var_query.filter(ChunksModel.doc_id.in_(doc_ids))

        # ── Order by cosine similarity (ascending distance = most similar) ─
        var_query = (
            var_query
            .order_by(ChunksModel.embedding.cosine_distance(query_embedding))
            .limit(var_top_k * 2)  # over-fetch for similarity filtering
        )

        var_results = var_query.all()

        # ── Build output list ──────────────────────────────────────────
        var_chunks: List[dict] = []
        for var_chunk, var_doc_title, var_similarity in var_results:
            var_sim = float(var_similarity) if var_similarity is not None else 0.0
            if var_sim < min_similarity:
                continue
            var_chunks.append(
                {
                    "chunk_id": var_chunk.chunk_id,
                    "doc_id": var_chunk.doc_id,
                    "doc_title": var_doc_title or "Unknown Document",
                    "chunk_text": var_chunk.chunk_text,
                    "chunk_index": var_chunk.chunk_index,
                    "similarity": round(var_sim, 4),
                    "metadata": var_chunk.metadata_,
                }
            )
            if len(var_chunks) >= var_top_k:
                break

        logger.debug(
            f"fn_search_similar_chunks: top_k={var_top_k} "
            f"doc_ids={doc_ids} returned={len(var_chunks)}"
        )
        return var_chunks

    except Exception as e:
        logger.error(f"fn_search_similar_chunks error: {e}")
        return []


def fn_search_by_query(
    db: Session,
    query: str,
    top_k: int = None,
    doc_ids: Optional[List[int]] = None,
    min_similarity: float = 0.0,
) -> List[dict]:
    """
    Convenience wrapper: embeds the query string then calls fn_search_similar_chunks.

    Use this when you have a raw text query (not a pre-computed embedding).
    """
    try:
        var_embedding = embedding_service.fn_embed_text(query)
    except Exception as e:
        logger.error(f"fn_search_by_query: embedding failed: {e}")
        return []

    return fn_search_similar_chunks(
        db=db,
        query_embedding=var_embedding,
        top_k=top_k,
        doc_ids=doc_ids,
        min_similarity=min_similarity,
    )