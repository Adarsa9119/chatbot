"""
chat_model.py — SQLAlchemy ORM model for chat_messages table.
Change Tracker:
  v1.0 — initial
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from config.database import Base


class ChatMessagesModel(Base):
    """
    ORM representation of the chat_messages table.
    Stores individual messages within a chat session.
    """

    __tablename__ = "chat_messages"

    message_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        Integer,
        ForeignKey("chat_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(20), nullable=False)  # 'user' | 'assistant'
    content = Column(Text, nullable=False)
    source_chunk_ids = Column(ARRAY(Integer), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("ChatSessionsModel", back_populates="messages")

    def __repr__(self) -> str:
        return f"<ChatMessagesModel id={self.message_id} session_id={self.session_id} role={self.role}>"