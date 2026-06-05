"""
email_service.py — Email sending via SMTP with HTML templates.
Supports: welcome, password reset, email verification, admin alert emails.
Change Tracker:
  v1.0 — initial
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from config.settings import settings
from config.logging_config import logger


# ── Read SMTP settings from .env ─────────────────────────────
# Add these to .env:
#   SMTP_HOST=smtp.gmail.com
#   SMTP_PORT=587
#   SMTP_USERNAME=your@email.com
#   SMTP_PASSWORD=your_app_password
#   SMTP_FROM_NAME=SecureDoc Chatbot
#   SMTP_FROM_EMAIL=no-reply@yourdomain.com
#   EMAIL_ENABLED=true
#
# For development, set EMAIL_ENABLED=false to skip actual sending.

SMTP_HOST = getattr(settings, "SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(getattr(settings, "SMTP_PORT", 587))
SMTP_USERNAME = getattr(settings, "SMTP_USERNAME", "")
SMTP_PASSWORD = getattr(settings, "SMTP_PASSWORD", "")
SMTP_FROM_NAME = getattr(settings, "SMTP_FROM_NAME", "SecureDoc Chatbot")
SMTP_FROM_EMAIL = getattr(settings, "SMTP_FROM_EMAIL", "no-reply@securedoc.local")
EMAIL_ENABLED = getattr(settings, "EMAIL_ENABLED", "false").lower() == "true"


class EmailService:
    """
    Sends transactional emails via SMTP.
    All outgoing emails are HTML with plain-text fallback.
    """

    def help_fn_send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        plain_body: Optional[str] = None,
    ) -> bool:
        """
        Core send function — builds MIME message and delivers via SMTP.
        Returns True on success, False on failure.
        Logs but never raises — email failure should not break API responses.
        """
        if not EMAIL_ENABLED:
            logger.info(
                f"[EMAIL DISABLED] Would send '{subject}' to {to_email}"
            )
            return True

        if not SMTP_USERNAME or not SMTP_PASSWORD:
            logger.warning("SMTP credentials not configured — email skipped")
            return False

        try:
            var_msg = MIMEMultipart("alternative")
            var_msg["Subject"] = subject
            var_msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
            var_msg["To"] = to_email

            if plain_body:
                var_msg.attach(MIMEText(plain_body, "plain"))
            var_msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as var_server:
                var_server.ehlo()
                var_server.starttls()
                var_server.login(SMTP_USERNAME, SMTP_PASSWORD)
                var_server.sendmail(SMTP_FROM_EMAIL, to_email, var_msg.as_string())

            logger.info(f"Email sent: '{subject}' → {to_email}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed — check credentials in .env")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"help_fn_send_email unexpected error: {e}")
            return False

    # ── Specific email senders ───────────────────────────────

    def fn_send_welcome_email(self, to_email: str, user_name: str) -> bool:
        """Send welcome email after successful signup."""
        var_subject = f"Welcome to SecureDoc, {user_name}!"
        var_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
            <div style="background:#1a3a5c; padding:20px; text-align:center;">
                <h1 style="color:white; margin:0;">SecureDoc RAG Chatbot</h1>
            </div>
            <div style="padding:30px;">
                <h2>Welcome, {user_name}!</h2>
                <p>Your account has been created successfully.</p>
                <p>You can now log in and start chatting with your documents.</p>
                <a href="{settings.FRONTEND_URL}/login"
                   style="background:#1a3a5c; color:white; padding:12px 24px;
                          text-decoration:none; border-radius:5px; display:inline-block;">
                   Go to Login
                </a>
            </div>
            <div style="padding:20px; color:#888; font-size:12px; text-align:center;">
                SecureDoc — Your confidential document assistant
            </div>
        </div>
        """
        var_plain = f"Welcome, {user_name}! Your SecureDoc account is ready. Login at {settings.FRONTEND_URL}/login"
        return self.help_fn_send_email(to_email, var_subject, var_html, var_plain)

    def fn_send_verification_email(
        self,
        to_email: str,
        user_name: str,
        verification_token: str,
    ) -> bool:
        """Send email verification link."""
        var_link = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        var_subject = "Verify your SecureDoc email address"
        var_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
            <div style="background:#1a3a5c; padding:20px; text-align:center;">
                <h1 style="color:white; margin:0;">SecureDoc RAG Chatbot</h1>
            </div>
            <div style="padding:30px;">
                <h2>Hi {user_name}, verify your email</h2>
                <p>Click the button below to verify your email address.
                   This link expires in 24 hours.</p>
                <a href="{var_link}"
                   style="background:#1a3a5c; color:white; padding:12px 24px;
                          text-decoration:none; border-radius:5px; display:inline-block;">
                   Verify Email
                </a>
                <p style="margin-top:20px; color:#666; font-size:12px;">
                    If you didn't create this account, ignore this email.
                </p>
            </div>
        </div>
        """
        var_plain = f"Verify your email: {var_link}"
        return self.help_fn_send_email(to_email, var_subject, var_html, var_plain)

    def fn_send_password_reset_email(
        self,
        to_email: str,
        user_name: str,
        reset_token: str,
    ) -> bool:
        """Send password reset link."""
        var_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        var_subject = "Reset your SecureDoc password"
        var_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
            <div style="background:#1a3a5c; padding:20px; text-align:center;">
                <h1 style="color:white; margin:0;">SecureDoc RAG Chatbot</h1>
            </div>
            <div style="padding:30px;">
                <h2>Password Reset Request</h2>
                <p>Hi {user_name}, we received a request to reset your password.</p>
                <p>Click the button below. This link expires in 30 minutes.</p>
                <a href="{var_link}"
                   style="background:#e53e3e; color:white; padding:12px 24px;
                          text-decoration:none; border-radius:5px; display:inline-block;">
                   Reset Password
                </a>
                <p style="margin-top:20px; color:#666; font-size:12px;">
                    If you didn't request this, you can safely ignore this email.
                    Your password will not be changed.
                </p>
            </div>
        </div>
        """
        var_plain = (
            f"Reset your SecureDoc password: {var_link}\n"
            f"Link expires in 30 minutes."
        )
        return self.help_fn_send_email(to_email, var_subject, var_html, var_plain)

    def fn_send_admin_alert(
        self,
        to_email: str,
        alert_title: str,
        alert_message: str,
    ) -> bool:
        """Send an admin security/system alert email."""
        var_subject = f"[SecureDoc Alert] {alert_title}"
        var_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
            <div style="background:#e53e3e; padding:20px; text-align:center;">
                <h1 style="color:white; margin:0;">⚠ SecureDoc Alert</h1>
            </div>
            <div style="padding:30px;">
                <h2>{alert_title}</h2>
                <p>{alert_message}</p>
            </div>
        </div>
        """
        return self.help_fn_send_email(to_email, var_subject, var_html, alert_message)


# ── Singleton ────────────────────────────────────────────────
email_service = EmailService()