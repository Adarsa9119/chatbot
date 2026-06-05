"""
email_verification_model.py — SQLAlchemy ORM model for the email_verifications table.
Stores email verification tokens sent after signup.
Change Tracker:
  v1.0 — initial
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from config.database import Base


class EmailVerificationsModel(Base):
    """
    ORM representation of the email_verifications table.

    Flow:
      1. User signs up → verification token generated + stored here
      2. Verification link emailed to user
      3. User clicks link → token validated (expiry + already_verified check)
      4. Token marked verified=True

    Notes:
      - Token expires in 24 hours (VERIFICATION_TOKEN_EXPIRE_HOURS in service)
      - Resending invalidates old unverified tokens for the same user
      - verified=True is permanent once set
    """

    __tablename__ = "email_verifications"

    verification_id = Column(
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

    user_email = Column(
        String(255),
        nullable=False,
        comment="Snapshot of the email address being verified",
    )

    token_hash = Column(
        Text,
        nullable=False,
        unique=True,
        comment="SHA-256 hash of the raw verification token",
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="Token expiry (24 hours from creation)",
    )

    verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="True once the email link has been successfully clicked",
    )

    verified_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when verification was completed",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Timestamp when the verification was requested (signup or resend)",
    )

    # ── Relationships ────────────────────────────────────────
    user = relationship(
        "UsersModel",
        foreign_keys=[user_id],
        back_populates=None,
    )

    def __repr__(self) -> str:
        return (
            f"<EmailVerificationsModel "
            f"id={self.verification_id} "
            f"user_id={self.user_id} "
            f"email={self.user_email} "
            f"verified={self.verified}>"
        )