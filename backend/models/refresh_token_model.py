"""
refresh_token_model.py — SQLAlchemy ORM model for refresh_tokens table.
FIXED: This table was missing from the original spec.
       Logout/revocation cannot work without it.
Change Tracker:
  v1.0 — initial (ADDED — not in original spec)
"""

from sqlalchemy import Column, Integer, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from config.database import Base


class RefreshTokensModel(Base):
    """
    ORM representation of the refresh_tokens table.
    Stores hashed refresh tokens for rotation and revocation on logout.
    """

    __tablename__ = "refresh_tokens"

    token_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash = Column(Text, nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("UsersModel", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<RefreshTokensModel id={self.token_id} user_id={self.user_id} revoked={self.revoked}>"