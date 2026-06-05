"""
send_email_task.py — Async-safe email dispatch wrappers for use
as FastAPI BackgroundTasks. Wraps email_service calls so any failure
doesn't break the HTTP response.

Change Tracker:
v1.0 — initial
"""

from config.logging_config import logger
from services.email_service import email_service


def fn_send_welcome_email_task(to_email: str, user_name: str) -> None:
    """
    Background task: send welcome email after successful signup.
    Called via: background_tasks.add_task(fn_send_welcome_email_task, ...)
    """
    try:
        var_result = email_service.fn_send_welcome_email(
            to_email=to_email,
            user_name=user_name,
        )
        if var_result:
            logger.info(f"Welcome email sent: {to_email}")
        else:
            logger.warning(f"Welcome email not sent (disabled or error): {to_email}")
    except Exception as e:
        logger.error(f"fn_send_welcome_email_task failed for {to_email}: {e}")


def fn_send_verification_email_task(
    to_email: str,
    user_name: str,
    verification_token: str,
) -> None:
    """
    Background task: send email verification link after signup.
    """
    try:
        var_result = email_service.fn_send_verification_email(
            to_email=to_email,
            user_name=user_name,
            verification_token=verification_token,
        )
        if var_result:
            logger.info(f"Verification email sent: {to_email}")
        else:
            logger.warning(f"Verification email not sent: {to_email}")
    except Exception as e:
        logger.error(f"fn_send_verification_email_task failed for {to_email}: {e}")


def fn_send_password_reset_email_task(
    to_email: str,
    user_name: str,
    reset_token: str,
) -> None:
    """
    Background task: send password reset link.
    """
    try:
        var_result = email_service.fn_send_password_reset_email(
            to_email=to_email,
            user_name=user_name,
            reset_token=reset_token,
        )
        if var_result:
            logger.info(f"Password reset email sent: {to_email}")
        else:
            logger.warning(f"Password reset email not sent: {to_email}")
    except Exception as e:
        logger.error(f"fn_send_password_reset_email_task failed for {to_email}: {e}")


def fn_send_admin_alert_task(
    to_email: str,
    alert_title: str,
    alert_message: str,
) -> None:
    """
    Background task: send admin security/system alert email.
    """
    try:
        var_result = email_service.fn_send_admin_alert(
            to_email=to_email,
            alert_title=alert_title,
            alert_message=alert_message,
        )
        if var_result:
            logger.info(f"Admin alert sent: '{alert_title}' → {to_email}")
        else:
            logger.warning(f"Admin alert not sent: {to_email}")
    except Exception as e:
        logger.error(f"fn_send_admin_alert_task failed for {to_email}: {e}")


# Alias used as a generic single entry point
fn_send_email_task = fn_send_welcome_email_task