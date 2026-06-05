"""
email_utils.py — HTML/plain-text email template builders.

These functions return (subject, html_body, plain_body) tuples.
Actual sending is handled by email_service.py / send_email_task.py.

Change Tracker:
    v1.0 — initial
"""

from __future__ import annotations

from typing import Tuple

from config.settings import settings

# ── Shared branding ───────────────────────────────────────────────────────────

APP_NAME = "DocChat"
SUPPORT_EMAIL = getattr(settings, "SUPPORT_EMAIL", "support@docchat.io")
BASE_URL = getattr(settings, "FRONTEND_URL", "http://localhost:5173")

_HTML_WRAPPER = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <style>
    body {{ font-family: Arial, sans-serif; background: #f4f6f9; margin: 0; padding: 0; }}
    .container {{ max-width: 560px; margin: 40px auto; background: #fff;
                  border-radius: 8px; overflow: hidden;
                  border: 1px solid #e0e0e0; }}
    .header {{ background: #1a1d23; padding: 24px 32px; }}
    .header h1 {{ color: #fff; margin: 0; font-size: 20px; letter-spacing: -0.3px; }}
    .body {{ padding: 32px; color: #333; font-size: 15px; line-height: 1.6; }}
    .btn {{ display: inline-block; margin: 24px 0; padding: 12px 28px;
            background: #4f8ef7; color: #fff; text-decoration: none;
            border-radius: 6px; font-weight: 600; font-size: 15px; }}
    .footer {{ padding: 20px 32px; background: #f4f6f9;
               font-size: 12px; color: #888; text-align: center; }}
    p {{ margin: 0 0 14px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header"><h1>🔒 {app_name}</h1></div>
    <div class="body">{body}</div>
    <div class="footer">
      © {app_name} · <a href="mailto:{support}">{support}</a><br>
      If you did not request this email, please ignore it.
    </div>
  </div>
</body>
</html>
"""


def _wrap_html(body_html: str) -> str:
    return _HTML_WRAPPER.format(
        app_name=APP_NAME,
        support=SUPPORT_EMAIL,
        body=body_html,
    )


# ── Email builders ────────────────────────────────────────────────────────────

def fn_build_verification_email(
    user_name: str,
    verification_token: str,
) -> Tuple[str, str, str]:
    """
    Build an email verification email.

    Args:
        user_name:           Recipient's display name.
        verification_token:  The one-time verification token.

    Returns:
        (subject, html_body, plain_body) tuple.
    """
    link = f"{BASE_URL}/verify-email?token={verification_token}"
    subject = f"Verify your {APP_NAME} email address"

    html_body = f"""
        <p>Hi {user_name},</p>
        <p>Thanks for signing up! Please verify your email address by clicking the button below.
           This link expires in <strong>24 hours</strong>.</p>
        <a class="btn" href="{link}">Verify Email Address</a>
        <p>Or copy this link into your browser:</p>
        <p style="word-break:break-all;font-size:13px;color:#555;">{link}</p>
    """

    plain_body = (
        f"Hi {user_name},\n\n"
        f"Please verify your email address by visiting:\n{link}\n\n"
        f"This link expires in 24 hours.\n\n"
        f"If you did not create a {APP_NAME} account, ignore this email."
    )

    return subject, _wrap_html(html_body), plain_body


def fn_build_password_reset_email(
    user_name: str,
    reset_token: str,
) -> Tuple[str, str, str]:
    """
    Build a password reset email.

    Args:
        user_name:    Recipient's display name.
        reset_token:  The one-time password reset token.

    Returns:
        (subject, html_body, plain_body) tuple.
    """
    link = f"{BASE_URL}/reset-password?token={reset_token}"
    subject = f"Reset your {APP_NAME} password"

    html_body = f"""
        <p>Hi {user_name},</p>
        <p>We received a request to reset your password. Click the button below to choose a new one.
           This link expires in <strong>1 hour</strong>.</p>
        <a class="btn" href="{link}">Reset Password</a>
        <p>Or copy this link into your browser:</p>
        <p style="word-break:break-all;font-size:13px;color:#555;">{link}</p>
        <p>If you didn't request a password reset, you can safely ignore this email —
           your password will not change.</p>
    """

    plain_body = (
        f"Hi {user_name},\n\n"
        f"Reset your password by visiting:\n{link}\n\n"
        f"This link expires in 1 hour.\n\n"
        f"If you did not request this, ignore this email."
    )

    return subject, _wrap_html(html_body), plain_body


def fn_build_welcome_email(user_name: str) -> Tuple[str, str, str]:
    """
    Build a welcome email sent after email verification succeeds.

    Args:
        user_name: Recipient's display name.

    Returns:
        (subject, html_body, plain_body) tuple.
    """
    dashboard_link = f"{BASE_URL}/dashboard"
    subject = f"Welcome to {APP_NAME}! 🎉"

    html_body = f"""
        <p>Hi {user_name},</p>
        <p>Your email has been verified and your {APP_NAME} account is now active.</p>
        <p>You can start uploading documents and asking questions right away.</p>
        <a class="btn" href="{dashboard_link}">Go to Dashboard</a>
        <p>If you have any questions, reach out at
           <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a>.</p>
    """

    plain_body = (
        f"Hi {user_name},\n\n"
        f"Welcome to {APP_NAME}! Your account is now active.\n\n"
        f"Visit your dashboard: {dashboard_link}\n\n"
        f"Questions? Contact us at {SUPPORT_EMAIL}."
    )

    return subject, _wrap_html(html_body), plain_body