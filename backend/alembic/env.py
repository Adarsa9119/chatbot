"""
Alembic environment — configures migrations for SQLAlchemy models.

Supports both offline (SQL script) and online (live DB) migration modes.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# ── Make 'backend/' importable ───────────────────────────────────────────────
# Alembic is run from the project root, so we add backend/ to the path.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from config.settings import settings
from config.database import Base

# ── Import all models so Alembic sees them ───────────────────────────────────
import models  # noqa: F401 — registers all SQLAlchemy models with Base.metadata

# ── Alembic Config object ────────────────────────────────────────────────────
config = context.config

# Set the database URL from settings (overrides alembic.ini sqlalchemy.url)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# ── Logging setup ─────────────────────────────────────────────────────────────
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Target metadata ───────────────────────────────────────────────────────────
target_metadata = Base.metadata


# ── Offline mode ─────────────────────────────────────────────────────────────

def run_migrations_offline() -> None:
    """
    Generate SQL migration scripts without connecting to the database.

    Useful for reviewing changes or applying migrations manually.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ── Online mode ───────────────────────────────────────────────────────────────

def run_migrations_online() -> None:
    """
    Apply migrations directly to a live database connection.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# ── Entry point ───────────────────────────────────────────────────────────────

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()