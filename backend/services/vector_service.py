"""
vector_service.py — High-level pgvector operations: store, search, delete embeddings.
Wraps crud_chunks with business logic and error handling.
Change Tracker:
  v1.0 — initial
"""

from sqlalchemy.orm import Session
from typing import List, Optional

from config.settings import settings
from config.logging_config import logger
from database.crud_chunks import (
    fn_bulk_create_chunks,
    fn_search_similar_chunks,
    fn_delete_chunks_by_doc,
    fn_count_chunks_by_doc,
)
from services.embedding_service import embedding_service


class VectorService:
    """
    High-level pgvector service:
      - Store embedded chunks for a document
      - Similarity search given a query string
      - Delete all chunks for a document
      - Retrieve chunk count per document
    """

    def fn_store_document_embeddings(
        self,
        db: Session,
        doc_id: int,
        chunks_data: List[dict],
    ) -> int:
        """
        Embed and store a list of text chunks for a document.
        chunks_data: list of { chunk_text, chunk_index, metadata }
        Returns count of stored chunks.

        Generates embeddings in batches of 32 for efficiency.
        """
        if not chunks_data:
            logger.warning(f"fn_store_document_embeddings: no chunks for doc_id={doc_id}")
            return 0

        try:
            var_texts = [item["chunk_text"] for item in chunks_data]
            var_embeddings = embedding_service.fn_embed_batch(var_texts)

            var_enriched = []
            for var_idx, var_item in enumerate(chunks_data):
                var_enriched.append({
                    "chunk_text": var_item["chunk_text"],
                    "chunk_index": var_item.get("chunk_index", var_idx),
                    "embedding": var_embeddings[var_idx],
                    "metadata": var_item.get("metadata", {}),
                })

            var_count = fn_bulk_create_chunks(db, doc_id, var_enriched)
            logger.info(f"Stored {var_count} embeddings for doc_id={doc_id}")
            return var_count

        except Exception as e:
            logger.error(f"fn_store_document_embeddings error: doc_id={doc_id} — {e}")
            raise

    def fn_search(
        self,
        db: Session,
        query: str,
        top_k: int = None,
        doc_ids: Optional[List[int]] = None,
    ) -> List[dict]:
        """
        Embed a query string and search pgvector for the most similar chunks.

        Args:
            query:   the user's natural language question
            top_k:   number of chunks to return (defaults to settings.TOP_K_CHUNKS)
            doc_ids: optional list of document IDs to restrict search to

        Returns list of {
            chunk_id, doc_id, doc_title, chunk_text,
            chunk_index, metadata, similarity
        }
        """
        var_k = top_k or settings.TOP_K_CHUNKS

        try:
            var_embedding = embedding_service.fn_embed_text(query)
            var_results = fn_search_similar_chunks(
                db=db,
                query_embedding=var_embedding,
                top_k=var_k,
                doc_ids=doc_ids,
            )
            logger.info(
                f"Vector search: query_len={len(query)} top_k={var_k} "
                f"doc_ids={doc_ids} results={len(var_results)}"
            )
            return var_results

        except Exception as e:
            logger.error(f"fn_search error: {e}")
            return []

    def fn_delete_document_vectors(self, db: Session, doc_id: int) -> int:
        """
        Delete all embedding vectors for a document.
        Called before reprocessing or deleting a document.
        Returns count of deleted chunks.
        """
        try:
            var_count = fn_delete_chunks_by_doc(db, doc_id)
            logger.info(f"Deleted {var_count} vectors for doc_id={doc_id}")
            return var_count
        except Exception as e:
            logger.error(f"fn_delete_document_vectors error: {e}")
            raise

    def fn_get_chunk_count(self, db: Session, doc_id: int) -> int:
        """Return the number of stored chunks for a document."""
        return fn_count_chunks_by_doc(db, doc_id)

    def fn_search_with_threshold(
        self,
        db: Session,
        query: str,
        threshold: float = 0.3,
        top_k: int = None,
        doc_ids: Optional[List[int]] = None,
    ) -> List[dict]:
        """
        Same as fn_search but filters out results below a similarity threshold.
        Useful when you want to return nothing rather than a poor match.
        threshold: minimum cosine similarity (0.0–1.0), default 0.3
        """
        var_results = self.fn_search(db, query, top_k, doc_ids)
        var_filtered = [r for r in var_results if r.get("similarity", 0) >= threshold]
        logger.info(
            f"Threshold filter: {len(var_results)} → {len(var_filtered)} chunks "
            f"(threshold={threshold})"
        )
        return var_filtered


# ── Singleton ────────────────────────────────────────────────
vector_service = VectorService()