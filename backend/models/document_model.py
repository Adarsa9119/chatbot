"""
document_model.py — SQLAlchemy ORM model for the documents table.
Change Tracker:
  v1.0 — initial
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from config.database import Base


class DocumentsModel(Base):
    """
    ORM representation of the documents table.
    Stores uploaded PDF metadata and processing status.
    """

    __tablename__ = "documents"

    doc_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(Text, nullable=False)
    file_size_kb = Column(Integer, nullable=True)
    ocr_required = Column(Boolean, default=False)
    status = Column(String(20), default="processing")  # processing | ready | failed
    error_message = Column(Text, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    uploader = relationship("UsersModel", foreign_keys=[uploaded_by])
    chunks = relationship("ChunksModel", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<DocumentsModel id={self.doc_id} title={self.title} status={self.status}>"