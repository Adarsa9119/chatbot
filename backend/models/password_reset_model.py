"""
password_reset_model.py — SQLAlchemy ORM model for the password_resets table.
Stores hashed password reset tokens with expiry and used flag.
Change Tracker:
  v1.0 — initial
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from config.database import Base


class PasswordResetsModel(Base):
    """
    ORM representation of the password_resets table.

    Flow:
      1. User requests password reset → token generated + stored here
      2. Token emailed to user as URL parameter
      3. User clicks link → token validated here (expiry + used check)
      4. Password updated → token marked used=True

    Security notes:
      - Only the SHA-256 hash of the raw token is stored (never plain token)
      - Tokens expire after 30 minutes (RESET_TOKEN_EXPIRE_MINUTES in service)
      - Once used=True the token can never be reused
      - One active token per user (old tokens overwritten on new request)
    """

    __tablename__ = "password_resets"

    reset_id = Column(
        Integer,
        primary_key=True,
        index=True,
        comment="Auto-incrementing primary key",
    )

    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK → users.user_id; cascades on user deletion",
    )

    token_hash = Column(
        Text,
        nullable=False,
        unique=True,
        comment="SHA-256 hash of the raw reset token (never store plain token)",
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="Token expiry timestamp (30 min from creation)",
    )

    used = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="True once the token has been consumed — prevents reuse",
    )

    ip_requested_from = Column(
        String(45),
        nullable=True,
        comment="IP address that triggered the reset request (for audit)",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Timestamp when the reset was requested",
    )

    used_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the token was successfully consumed",
    )

    # ── Relationships ────────────────────────────────────────
    user = relationship(
        "UsersModel",
        foreign_keys=[user_id],
        back_populates=None,   # UsersModel does not need a back_ref for this
    )

    def __repr__(self) -> str:
        return (
            f"<PasswordResetsModel "
            f"id={self.reset_id} "
            f"user_id={self.user_id} "
            f"used={self.used} "
            f"expires_at={self.expires_at}>"
        )