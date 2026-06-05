"""
session.py — SQLAlchemy session factory, FastAPI dependency, and
             transaction context manager helpers.
Change Tracker:
  v1.0 — initial
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import sessionmaker, Session

from database.connection import engine
from config.logging_config import logger


# ── Session factory ──────────────────────────────────────────
# autocommit=False → we control transactions explicitly
# autoflush=False  → prevents accidental premature flushes mid-operation
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,     # keep objects usable after commit
)


# ── FastAPI dependency ───────────────────────────────────────
def fn_get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session per request.

    Usage in a router:
        db: Session = Depends(fn_get_db)

    Behaviour:
      - Opens a session at the start of the request
      - Yields it to the route handler
      - Closes it after the response is sent (even on exception)

    NOTE: Commit/rollback is the responsibility of the calling code
          (service or CRUD function). This dependency only opens/closes.
    """
    var_db = SessionLocal()
    try:
        yield var_db
    except Exception as e:
        var_db.rollback()
        logger.error(f"fn_get_db: session rolled back due to exception: {e}")
        raise
    finally:
        var_db.close()


# ── Context manager for background tasks ────────────────────
@contextmanager
def fn_get_db_context() -> Generator[Session, None, None]:
    """
    Context manager version of the DB session.
    Use this in background tasks (not FastAPI route handlers).

    Usage:
        with fn_get_db_context() as db:
            fn_create_chunk(db, ...)

    Unlike fn_get_db (which is a FastAPI Depends generator),
    this can be used anywhere without the FastAPI DI system.
    """
    var_db = SessionLocal()
    try:
        yield var_db
        var_db.commit()
    except Exception as e:
        var_db.rollback()
        logger.error(f"fn_get_db_context: rolled back — {e}")
        raise
    finally:
        var_db.close()


# ── Standalone session (background tasks that handle own commits) ─
def fn_get_standalone_db() -> Session:
    """
    Return a raw Session not managed by any context manager.
    Caller is responsible for commit(), rollback(), and close().

    Use ONLY in background tasks (e.g. fn_process_document_task)
    where you need fine-grained control over the lifecycle.

    Example:
        db = fn_get_standalone_db()
        try:
            fn_update_document_status(db, doc_id, 'ready')
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    """
    return SessionLocal()


# ── Transaction helper ───────────────────────────────────────
def fn_safe_commit(db: Session) -> bool:
    """
    Attempt to commit; roll back on failure.
    Returns True on success, False on failure.
    Use when you want to handle commit errors gracefully
    without propagating an exception.
    """
    try:
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"fn_safe_commit: rollback triggered — {e}")
        return False


def fn_safe_flush(db: Session) -> bool:
    """
    Flush pending changes to DB within the current transaction
    (makes IDs available) without committing.
    Returns True on success, False on failure.
    """
    try:
        db.flush()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"fn_safe_flush: rollback triggered — {e}")
        return False