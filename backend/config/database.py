"""
database.py — SQLAlchemy engine, session factory, Base model.
Change Tracker:
  v1.0 — initial
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from typing import Generator
from config.settings import settings
from config.logging_config import logger


# ── Engine ──────────────────────────────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.APP_DEBUG,
)

# ── Session factory ─────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── Base class for all models ────────────────────────────────
Base = declarative_base()


def fn_get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency — yields a DB session and closes it after use.
    Usage: db: Session = Depends(fn_get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def fn_check_db_connection() -> bool:
    """
    Health check — verifies DB is reachable.
    Returns True if connection succeeds, False otherwise.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"DB connection failed: {e}")
        return False


def fn_create_all_tables() -> None:
    """
    Creates all tables defined in models if they don't exist.
    Called at startup — safe to run multiple times.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("All tables created / verified.")
    except Exception as e:
        logger.error(f"Table creation failed: {e}")
        raise