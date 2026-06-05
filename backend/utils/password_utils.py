"""
password_utils.py — Password hashing, verification, and strength validation.

Uses passlib with bcrypt.

Change Tracker:
    v1.0 — initial
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from passlib.context import CryptContext

from config.logging_config import logger

# ── Passlib context ───────────────────────────────────────────────────────────

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Hashing ───────────────────────────────────────────────────────────────────

def fn_hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    Args:
        plain_password: The raw password string.

    Returns:
        The bcrypt hash string.
    """
    return _pwd_context.hash(plain_password)


def fn_verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a bcrypt hash.

    Args:
        plain_password:   The raw password to check.
        hashed_password:  The stored bcrypt hash.

    Returns:
        True if they match, False otherwise.
    """
    return _pwd_context.verify(plain_password, hashed_password)


# ── Strength validation ───────────────────────────────────────────────────────

@dataclass
class PasswordStrengthResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    score: int = 0  # 0–5


_RULES = [
    (r".{8,}", "at least 8 characters"),
    (r"[A-Z]", "at least one uppercase letter"),
    (r"[a-z]", "at least one lowercase letter"),
    (r"\d", "at least one number"),
    (r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\;'/`~]", "at least one special character"),
]


def fn_validate_password_strength(password: str) -> PasswordStrengthResult:
    """
    Check a password against the project's strength rules.

    Rules (each adds 1 to score):
        1. At least 8 characters
        2. At least one uppercase letter
        3. At least one lowercase letter
        4. At least one digit
        5. At least one special character

    Args:
        password: The plain-text password to evaluate.

    Returns:
        PasswordStrengthResult with is_valid (True if score == 5),
        a list of unmet rule descriptions, and a score 0–5.
    """
    errors: List[str] = []
    score = 0

    for pattern, description in _RULES:
        if re.search(pattern, password):
            score += 1
        else:
            errors.append(f"Password must contain {description}.")

    return PasswordStrengthResult(
        is_valid=(score == len(_RULES)),
        errors=errors,
        score=score,
    )