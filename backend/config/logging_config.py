"""
logging_config.py — Loguru-based logging setup.
Change Tracker:
  v1.0 — initial
"""

import sys
from pathlib import Path
from loguru import logger
from config.settings import settings


def fn_setup_logging() -> None:
    """
    Configure loguru logger.
    Logs to console (colored) and to file with rotation.
    """
    log_path = Path(settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.remove()  # remove default handler

    # Console — colorized
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
               "<level>{message}</level>",
        colorize=True,
    )

    # File — with rotation (10 MB) and retention (7 days)
    logger.add(
        str(log_path),
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} — {message}",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
    )

    logger.info(f"Logging initialized — level={settings.LOG_LEVEL}")


# ── Export logger for use in other modules ──────────────────
__all__ = ["logger", "fn_setup_logging"]