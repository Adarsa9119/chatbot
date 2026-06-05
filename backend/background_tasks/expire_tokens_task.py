"""
expire_tokens_task.py — Periodic task to hard-delete expired tokens
from the database to prevent table bloat.

Change Tracker:
v1.0 — initial
"""

from config.logging_config import logger
from database.session import fn_get_standalone_db
from database.crud_refresh_tokens import fn_delete_expired_refresh_tokens
from database.crud_password_resets import fn_delete_expired_reset_tokens
from database.crud_email_verifications import fn_delete_expired_verifications


def fn_expire_tokens_task() -> None:
    """
    Hard-delete all expired tokens across all token tables.

    Tables cleaned:
    - refresh_tokens: expired OR revoked
    - password_resets: expired AND used
    - email_verifications: expired AND unverified (>7 days old)

    Safe to run multiple times; uses server-side timestamp comparisons.
    Recommended schedule: every 6–24 hours.
    """
    logger.info("fn_expire_tokens_task: starting token expiry cleanup")
    db = fn_get_standalone_db()
    try:
        var_rt_count = fn_delete_expired_refresh_tokens(db)
        var_pr_count = fn_delete_expired_reset_tokens(db)
        var_ev_count = fn_delete_expired_verifications(db)

        logger.info(
            f"fn_expire_tokens_task complete — "
            f"refresh_tokens={var_rt_count} "
            f"password_resets={var_pr_count} "
            f"email_verifications={var_ev_count}"
        )
    except Exception as e:
        logger.error(f"fn_expire_tokens_task error: {e}")
    finally:
        db.close()