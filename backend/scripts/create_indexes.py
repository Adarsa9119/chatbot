"""
create_indexes.py — Create PostgreSQL indexes including the pgvector HNSW index.
Run this once after initial table creation for optimal vector search performance.

Usage:
    python scripts/create_indexes.py

Change Tracker:
v1.0 — initial
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.database import engine
from config.logging_config import fn_setup_logging, logger
from sqlalchemy import text


INDEXES = [
    # ── pgvector HNSW index for fast approximate nearest-neighbor search ──
    # HNSW is recommended over IVFFlat for latency-sensitive applications.
    # m=16, ef_construction=64 are good defaults; tune for your dataset size.
    (
        "idx_chunks_embedding_hnsw",
        """
        CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
        ON chunks USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
        """,
    ),
    # ── Standard B-tree indexes ──────────────────────────────────────────
    (
        "idx_chunks_doc_id",
        "CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks (doc_id);",
    ),
    (
        "idx_chat_messages_session_id",
        "CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages (session_id);",
    ),
    (
        "idx_chat_sessions_user_id",
        "CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions (user_id);",
    ),
    (
        "idx_documents_status",
        "CREATE INDEX IF NOT EXISTS idx_documents_status ON documents (status);",
    ),
    (
        "idx_documents_uploaded_by",
        "CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by ON documents (uploaded_by);",
    ),
    (
        "idx_audit_logs_user_id",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs (user_id);",
    ),
    (
        "idx_audit_logs_action",
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs (action);",
    ),
    (
        "idx_refresh_tokens_user_id",
        "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens (user_id);",
    ),
    (
        "idx_password_resets_user_id",
        "CREATE INDEX IF NOT EXISTS idx_password_resets_user_id ON password_resets (user_id);",
    ),
    (
        "idx_email_verifications_user_id",
        "CREATE INDEX IF NOT EXISTS idx_email_verifications_user_id ON email_verifications (user_id);",
    ),
]


def fn_create_indexes() -> None:
    fn_setup_logging()
    logger.info("Creating database indexes...")

    with engine.connect() as conn:
        for var_name, var_sql in INDEXES:
            try:
                conn.execute(text(var_sql))
                conn.commit()
                print(f"[OK] {var_name}")
                logger.info(f"Index created/verified: {var_name}")
            except Exception as e:
                print(f"[WARN] {var_name}: {e}")
                logger.warning(f"Index {var_name} failed: {e}")

    print("\nAll indexes processed.")


if __name__ == "__main__":
    fn_create_indexes()