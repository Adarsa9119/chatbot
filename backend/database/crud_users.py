"""
crud_users.py — Database operations for the users table.
Change Tracker:
  v1.0 — initial
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from models.user_model import UsersModel
from config.logging_config import logger


def fn_get_user_by_id(db: Session, user_id: int) -> Optional[UsersModel]:
    """Fetch a user by primary key."""
    try:
        return db.query(UsersModel).filter(UsersModel.user_id == user_id).first()
    except Exception as e:
        logger.error(f"fn_get_user_by_id error: {e}")
        return None


def fn_get_user_by_email(db: Session, user_email: str) -> Optional[UsersModel]:
    """Fetch a user by email address."""
    try:
        return db.query(UsersModel).filter(UsersModel.user_email == user_email).first()
    except Exception as e:
        logger.error(f"fn_get_user_by_email error: {e}")
        return None


def fn_get_user_by_username(db: Session, user_name: str) -> Optional[UsersModel]:
    """Fetch a user by username."""
    try:
        return db.query(UsersModel).filter(UsersModel.user_name == user_name).first()
    except Exception as e:
        logger.error(f"fn_get_user_by_username error: {e}")
        return None


def fn_create_user(
    db: Session,
    user_name: str,
    user_email: str,
    hashed_password: str,
    user_role: str,
) -> UsersModel:
    """Insert a new user record."""
    try:
        var_user = UsersModel(
            user_name=user_name,
            user_email=user_email,
            user_password=hashed_password,
            user_role=user_role,
        )
        db.add(var_user)
        db.commit()
        db.refresh(var_user)
        logger.info(f"User created: id={var_user.user_id} email={user_email}")
        return var_user
    except Exception as e:
        db.rollback()
        logger.error(f"fn_create_user error: {e}")
        raise


def fn_update_user(
    db: Session,
    user_id: int,
    **kwargs,
) -> Optional[UsersModel]:
    """Update user fields. Only updates fields provided in kwargs."""
    try:
        var_user = fn_get_user_by_id(db, user_id)
        if not var_user:
            return None
        for var_field, var_value in kwargs.items():
            if var_value is not None:
                setattr(var_user, var_field, var_value)
        db.commit()
        db.refresh(var_user)
        return var_user
    except Exception as e:
        db.rollback()
        logger.error(f"fn_update_user error: {e}")
        raise


def fn_get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[UsersModel]:
    """Admin: list all users with pagination."""
    try:
        return db.query(UsersModel).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"fn_get_all_users error: {e}")
        return []


def fn_count_users(db: Session) -> int:
    """Count total users."""
    try:
        return db.query(func.count(UsersModel.user_id)).scalar() or 0
    except Exception as e:
        logger.error(f"fn_count_users error: {e}")
        return 0


def fn_delete_user(db: Session, user_id: int) -> bool:
    """Delete a user by ID."""
    try:
        var_user = fn_get_user_by_id(db, user_id)
        if not var_user:
            return False
        db.delete(var_user)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"fn_delete_user error: {e}")
        raise