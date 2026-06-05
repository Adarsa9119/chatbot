"""
cleanup_task.py — Periodic cleanup of expired tokens and temp files.
Should be scheduled or called from a startup event / cron.

Change Tracker:
v1.0 — initial
"""

import os
from pathlib import Path
from datetime import datetime, timezone

from config.logging_config import logger
from config.settings import settings
from database.session import fn_get_standalone_db
from database.crud_refresh_tokens import fn_delete_expired_refresh_tokens
from database.crud_password_resets import fn_delete_expired_reset_tokens
from database.crud_email_verifications import fn_delete_expired_verifications


def fn_cleanup_task() -> None:
    """
    Cleanup task — runs periodically (e.g. daily).

    Actions:
    1. Delete expired refresh tokens from DB
    2. Delete expired/used password reset tokens
    3. Delete expired email verification tokens
    4. Remove temp upload files older than 24 hours
    """
    logger.info("Cleanup task started")
    db = fn_get_standalone_db()
    try:
        # ── Token cleanup ───────────────────────────────────────────────
        var_rt = fn_delete_expired_refresh_tokens(db)
        var_pr = fn_delete_expired_reset_tokens(db)
        var_ev = fn_delete_expired_verifications(db)

        logger.info(
            f"Cleanup DB: refresh_tokens={var_rt} "
            f"password_resets={var_pr} email_verifications={var_ev}"
        )

        # ── Temp file cleanup ───────────────────────────────────────────
        var_temp_dir = Path(settings.TEMP_DIR)
        var_cleaned = 0
        if var_temp_dir.exists():
            var_now = datetime.now(timezone.utc).timestamp()
            for var_file in var_temp_dir.iterdir():
                if var_file.is_file():
                    var_age_hours = (var_now - var_file.stat().st_mtime) / 3600
                    if var_age_hours > 24:
                        try:
                            var_file.unlink()
                            var_cleaned += 1
                        except Exception as e:
                            logger.warning(f"Could not delete temp file {var_file}: {e}")

        logger.info(f"Cleanup temp files: deleted={var_cleaned}")
        logger.info("Cleanup task complete")

    except Exception as e:
        logger.error(f"fn_cleanup_task error: {e}")
    finally:
        db.close()


def fn_cleanup_failed_uploads() -> None:
    """
    Move documents in 'failed' status with no file to the failed directory.
    Run periodically to keep uploads/ tidy.
    """
    from database.crud_documents import fn_get_all_documents, fn_update_document_status

    db = fn_get_standalone_db()
    try:
        var_failed_dir = Path(settings.FAILED_DIR)
        var_failed_dir.mkdir(parents=True, exist_ok=True)

        var_docs = fn_get_all_documents(db)
        for var_doc in var_docs:
            if var_doc.status == "failed":
                var_path = Path(var_doc.file_path)
                if var_path.exists():
                    var_dest = var_failed_dir / var_path.name
                    try:
                        var_path.rename(var_dest)
                        logger.info(f"Moved failed doc file: {var_path} → {var_dest}")
                    except Exception as e:
                        logger.warning(f"Could not move failed file {var_path}: {e}")
    except Exception as e:
        logger.error(f"fn_cleanup_failed_uploads error: {e}")
    finally:
        db.close()