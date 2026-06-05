"""
session_model.py — SQLAlchemy ORM model for chat_sessions table.
Change Tracker:
  v1.0 — initial
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from config.database import Base


class ChatSessionsModel(Base):
    """
    ORM representation of the chat_sessions table.
    One session = one conversation thread per user.
    """

    __tablename__ = "chat_sessions"

    session_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=True, default="New Chat")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("UsersModel", foreign_keys=[user_id])
    messages = relationship("ChatMessagesModel", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ChatSessionsModel id={self.session_id} user_id={self.user_id} title={self.title}>"