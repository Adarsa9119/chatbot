"""
chunk_model.py — SQLAlchemy ORM model for the chunks table (pgvector).
Change Tracker:
  v1.0 — initial
"""

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from config.database import Base
from config.settings import settings


class ChunksModel(Base):
    """
    ORM representation of the chunks table.
    Stores text chunks with 384-dim pgvector embeddings.
    """

    __tablename__ = "chunks"

    chunk_id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(
        Integer,
        ForeignKey("documents.doc_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=True)
    embedding = Column(Vector(settings.EMBEDDING_DIMENSION), nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("DocumentsModel", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<ChunksModel id={self.chunk_id} doc_id={self.doc_id} idx={self.chunk_index}>"