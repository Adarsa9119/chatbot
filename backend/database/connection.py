"""
connection.py — SQLAlchemy engine creation, pgvector extension setup,
                and database connectivity utilities.
Change Tracker:
  v1.0 — initial
"""

from sqlalchemy import create_engine, text, event
from sqlalchemy.pool import QueuePool
from typing import Optional

from config.settings import settings
from config.logging_config import logger


# ── Engine singleton ─────────────────────────────────────────
# Created once at module import — shared across all requests.
# pool_pre_ping=True re-validates connections before use (handles stale TCP).
# pool_size=10 / max_overflow=20 → up to 30 concurrent DB connections.
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,          # recycle connections after 1 hour
    pool_timeout=30,            # wait max 30s for a connection from pool
    echo=settings.APP_DEBUG,    # log SQL in debug mode only
    connect_args={
        # PostgreSQL: set application_name for pg_stat_activity visibility
        "application_name": "SecureDocChatbot",
    },
)


# ── Event listener: set ivfflat.probes per connection ────────
# FIXED: pgvector IVFFlat needs probes set each session for recall quality.
# probes=10 balances speed vs accuracy for up to ~1M chunks.
@event.listens_for(engine, "connect")
def fn_set_pg_session_params(dbapi_connection, connection_record):
    """
    Set PostgreSQL session-level parameters on every new connection.
    ivfflat.probes=10 → controls how many IVF clusters are searched
                        during approximate nearest-neighbour queries.
    """
    try:
        with dbapi_connection.cursor() as var_cursor:
            var_cursor.execute("SET ivfflat.probes = 10")
        dbapi_connection.commit()
    except Exception as e:
        logger.warning(f"fn_set_pg_session_params: {e}")


# ── Connectivity helpers ─────────────────────────────────────

def fn_check_connection() -> bool:
    """
    Lightweight connectivity check — runs SELECT 1.
    Used by the health endpoint and startup lifespan.
    Returns True if database is reachable, False otherwise.
    """
    try:
        with engine.connect() as var_conn:
            var_conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"fn_check_connection failed: {e}")
        return False


def fn_ensure_pgvector_extension() -> bool:
    """
    Create the pgvector extension if it doesn't already exist.
    Must be run as a PostgreSQL superuser (postgres).
    Called once at startup lifespan.
    Returns True on success, False on failure.
    """
    try:
        with engine.connect() as var_conn:
            var_conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            var_conn.commit()
        logger.info("pgvector extension: ready")
        return True
    except Exception as e:
        logger.error(
            f"fn_ensure_pgvector_extension failed: {e}\n"
            f"Run manually: psql -U postgres -d {settings.DB_NAME} "
            f"-c 'CREATE EXTENSION IF NOT EXISTS vector;'"
        )
        return False


def fn_create_vector_index() -> bool:
    """
    Create the IVFFlat cosine similarity index on chunks.embedding.
    FIXED: Without this index, every similarity search is O(n) — unusably slow.

    Safe to run multiple times (IF NOT EXISTS).
    Should be called after the first batch of documents are processed
    (IVFFlat needs at least 'lists' rows to build meaningfully).

    lists=100 is appropriate for up to ~1M chunks.
    For larger datasets: lists = sqrt(total_rows).
    """
    try:
        with engine.connect() as var_conn:
            var_conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_chunks_embedding
                ON chunks
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """))
            var_conn.commit()
        logger.info("pgvector IVFFlat index: ready")
        return True
    except Exception as e:
        logger.warning(
            f"fn_create_vector_index: {e} "
            f"(non-critical if chunks table is empty — re-run after first upload)"
        )
        return False


def fn_get_db_version() -> Optional[str]:
    """Return the PostgreSQL version string (for health/debug output)."""
    try:
        with engine.connect() as var_conn:
            var_result = var_conn.execute(text("SELECT version()"))
            return var_result.scalar()
    except Exception as e:
        logger.error(f"fn_get_db_version: {e}")
        return None


def fn_get_table_row_counts() -> dict:
    """
    Return row counts for all main tables.
    Used by admin dashboard stats endpoint.
    """
    var_tables = [
        "users", "documents", "chunks",
        "chat_sessions", "chat_messages",
        "refresh_tokens", "audit_logs",
    ]
    var_counts = {}
    try:
        with engine.connect() as var_conn:
            for var_table in var_tables:
                try:
                    var_result = var_conn.execute(
                        text(f"SELECT COUNT(*) FROM {var_table}")
                    )
                    var_counts[var_table] = var_result.scalar() or 0
                except Exception:
                    var_counts[var_table] = -1  # table may not exist yet
    except Exception as e:
        logger.error(f"fn_get_table_row_counts: {e}")
    return var_counts


def fn_dispose_engine() -> None:
    """
    Close all pooled connections.
    Called during application shutdown lifespan.
    """
    engine.dispose()
    logger.info("Database engine disposed — all connections closed")