"""
audit_log_model.py — SQLAlchemy ORM model for audit_logs table.
Change Tracker:
  v1.0 — initial
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from config.database import Base


class AuditLogsModel(Base):
    """
    ORM representation of the audit_logs table.
    Records all significant actions for compliance and auditing.
    """

    __tablename__ = "audit_logs"

    log_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action = Column(String(100), nullable=False)    # e.g. 'document_upload', 'user_login'
    resource_type = Column(String(50), nullable=True)  # 'document', 'user', 'session'
    resource_id = Column(Integer, nullable=True)
    details = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("UsersModel", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<AuditLogsModel id={self.log_id} action={self.action} user_id={self.user_id}>"