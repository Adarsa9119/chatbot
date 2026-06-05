"""
reranker.py — Cross-encoder reranker for improving RAG chunk relevance.

After vector search returns top-K chunks by cosine similarity,
the reranker scores each chunk against the query using a more expensive
cross-encoder model to improve precision before sending to the LLM.

Strategy used: lightweight cross-encoder (cross-encoder/ms-marco-MiniLM-L-6-v2)
or simple keyword overlap scoring as fallback.

Change Tracker:
v1.0 — initial
"""

from typing import List, Optional
from config.settings import settings
from config.logging_config import logger


# ── Optional cross-encoder model (loaded lazily) ───────────────────────
_cross_encoder_model = None

def _fn_load_cross_encoder():
    """Lazily load the cross-encoder model. Returns None if unavailable."""
    global _cross_encoder_model
    if _cross_encoder_model is not None:
        return _cross_encoder_model
    try:
        from sentence_transformers import CrossEncoder
        _cross_encoder_model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2",
            max_length=512,
        )
        logger.info("Cross-encoder reranker loaded successfully")
        return _cross_encoder_model
    except Exception as e:
        logger.warning(
            f"Cross-encoder not available ({e}), will use keyword fallback reranker"
        )
        return None


def fn_rerank_chunks(
    query: str,
    chunks: List[dict],
    top_n: Optional[int] = None,
    use_cross_encoder: bool = True,
) -> List[dict]:
    """
    Rerank retrieved chunks by relevance to the query.

    Args:
        query:            The user's question.
        chunks:           List of chunk dicts from vector_service.fn_search().
                          Each dict must have at least 'chunk_text'.
        top_n:            How many chunks to return after reranking.
                          Defaults to settings.TOP_K_CHUNKS.
        use_cross_encoder: If False, skip cross-encoder and use keyword fallback.

    Returns:
        List of chunks sorted by reranking score (best first), length ≤ top_n.

    Each chunk dict is augmented with 'rerank_score'.
    """
    if not chunks:
        return []

    var_top_n = top_n or settings.TOP_K_CHUNKS

    if use_cross_encoder:
        var_model = _fn_load_cross_encoder()
        if var_model is not None:
            return _fn_cross_encoder_rerank(query, chunks, var_top_n, var_model)

    # Fallback: keyword overlap scoring
    return _fn_keyword_rerank(query, chunks, var_top_n)


# ── Cross-encoder reranker ─────────────────────────────────────────────

def _fn_cross_encoder_rerank(
    query: str,
    chunks: List[dict],
    top_n: int,
    model,
) -> List[dict]:
    """Score all chunks against the query using a cross-encoder model."""
    try:
        var_pairs = [(query, c["chunk_text"]) for c in chunks]
        var_scores = model.predict(var_pairs)

        for var_chunk, var_score in zip(chunks, var_scores):
            var_chunk["rerank_score"] = float(var_score)

        var_reranked = sorted(chunks, key=lambda c: c["rerank_score"], reverse=True)

        logger.debug(
            f"Cross-encoder reranked {len(chunks)} → top {top_n}: "
            f"scores={[round(c['rerank_score'], 3) for c in var_reranked[:top_n]]}"
        )
        return var_reranked[:top_n]

    except Exception as e:
        logger.warning(f"Cross-encoder rerank failed ({e}), using keyword fallback")
        return _fn_keyword_rerank(query, chunks, top_n)


# ── Keyword overlap fallback reranker ──────────────────────────────────

def _fn_keyword_rerank(query: str, chunks: List[dict], top_n: int) -> List[dict]:
    """
    Lightweight fallback: score by number of query keywords found in chunk.
    Used when cross-encoder is unavailable or fails.
    """
    import re
    var_query_words = set(re.findall(r"\b\w{3,}\b", query.lower()))

    if not var_query_words:
        return chunks[:top_n]

    for var_chunk in chunks:
        var_chunk_words = set(
            re.findall(r"\b\w{3,}\b", var_chunk.get("chunk_text", "").lower())
        )
        var_overlap = len(var_query_words & var_chunk_words)
        # Combine with original similarity score (weighted)
        var_sim = var_chunk.get("similarity", 0.5)
        var_chunk["rerank_score"] = (var_overlap * 0.1) + (var_sim * 0.9)

    var_reranked = sorted(chunks, key=lambda c: c["rerank_score"], reverse=True)
    logger.debug(f"Keyword reranked {len(chunks)} → top {top_n}")
    return var_reranked[:top_n]