"""
crud_chunks.py — Database operations for the chunks table (pgvector).
Change Tracker:
  v1.0 — initial
"""

from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import Optional, List
from models.chunk_model import ChunksModel
from config.logging_config import logger
from config.settings import settings


def fn_create_chunk(
    db: Session,
    doc_id: int,
    chunk_text: str,
    chunk_index: int,
    embedding: List[float],
    metadata: Optional[dict] = None,
) -> ChunksModel:
    """Insert a single chunk with its embedding."""
    try:
        var_chunk = ChunksModel(
            doc_id=doc_id,
            chunk_text=chunk_text,
            chunk_index=chunk_index,
            embedding=embedding,
            metadata_=metadata or {},
        )
        db.add(var_chunk)
        db.commit()
        db.refresh(var_chunk)
        return var_chunk
    except Exception as e:
        db.rollback()
        logger.error(f"fn_create_chunk error: {e}")
        raise


def fn_bulk_create_chunks(
    db: Session,
    doc_id: int,
    chunks_data: List[dict],
) -> int:
    """
    Bulk insert chunks for a document.
    chunks_data: list of { chunk_text, chunk_index, embedding, metadata }
    Returns count of inserted chunks.
    """
    try:
        temp_var_chunk_list = [
            ChunksModel(
                doc_id=doc_id,
                chunk_text=item["chunk_text"],
                chunk_index=item["chunk_index"],
                embedding=item["embedding"],
                metadata_=item.get("metadata", {}),
            )
            for item in chunks_data
        ]
        db.bulk_save_objects(temp_var_chunk_list)
        db.commit()
        logger.info(f"Bulk inserted {len(temp_var_chunk_list)} chunks for doc_id={doc_id}")
        return len(temp_var_chunk_list)
    except Exception as e:
        db.rollback()
        logger.error(f"fn_bulk_create_chunks error: {e}")
        raise


def fn_search_similar_chunks(
    db: Session,
    query_embedding: List[float],
    top_k: int = 5,
    doc_ids: Optional[List[int]] = None,
) -> List[dict]:
    """
    Cosine similarity search using pgvector <=> operator.
    Returns top_k most relevant chunks with their document info.
    FIXED: Must set ivfflat.probes each session for performance.
    """
    try:
        # Set IVFFlat probes for this session
        db.execute(text("SET ivfflat.probes = 10"))

        var_embedding_str = f"[{','.join(str(x) for x in query_embedding)}]"

        if doc_ids:
            var_doc_filter = f"AND c.doc_id = ANY(ARRAY{doc_ids})"
        else:
            var_doc_filter = ""

        var_query = text(f"""
            SELECT
                c.chunk_id,
                c.doc_id,
                c.chunk_text,
                c.chunk_index,
                c.metadata,
                d.title AS doc_title,
                1 - (c.embedding <=> :embedding::vector) AS similarity
            FROM chunks c
            JOIN documents d ON d.doc_id = c.doc_id
            WHERE d.status = 'ready'
            {var_doc_filter}
            ORDER BY c.embedding <=> :embedding::vector
            LIMIT :top_k
        """)

        var_result = db.execute(
            var_query,
            {"embedding": var_embedding_str, "top_k": top_k},
        )

        var_rows = var_result.fetchall()
        return [
            {
                "chunk_id": row.chunk_id,
                "doc_id": row.doc_id,
                "chunk_text": row.chunk_text,
                "chunk_index": row.chunk_index,
                "metadata": row.metadata,
                "doc_title": row.doc_title,
                "similarity": float(row.similarity),
            }
            for row in var_rows
        ]
    except Exception as e:
        logger.error(f"fn_search_similar_chunks error: {e}")
        return []


def fn_delete_chunks_by_doc(db: Session, doc_id: int) -> int:
    """Delete all chunks for a document. Returns count deleted."""
    try:
        var_count = db.query(ChunksModel).filter(ChunksModel.doc_id == doc_id).delete()
        db.commit()
        return var_count
    except Exception as e:
        db.rollback()
        logger.error(f"fn_delete_chunks_by_doc error: {e}")
        raise


def fn_count_chunks_by_doc(db: Session, doc_id: int) -> int:
    """Count chunks belonging to a document."""
    try:
        return db.query(func.count(ChunksModel.chunk_id)).filter(ChunksModel.doc_id == doc_id).scalar() or 0
    except Exception as e:
        logger.error(f"fn_count_chunks_by_doc error: {e}")
        return 0