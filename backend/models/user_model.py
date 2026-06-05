"""
user_model.py — SQLAlchemy ORM model for the users table.
Change Tracker:
  v1.0 — initial
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from config.database import Base


class UsersModel(Base):
    """
    ORM representation of the users table.
    Stores admin and user accounts.
    """

    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String(100), nullable=False)
    user_email = Column(String(255), unique=True, nullable=False, index=True)
    user_password = Column(Text, nullable=False)
    user_role = Column(String(20), nullable=False, default="user")  # 'admin' | 'user'
    profile_image_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<UsersModel id={self.user_id} email={self.user_email} role={self.user_role}>"