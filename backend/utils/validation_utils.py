"""
validation_utils.py — Input validation and sanitisation helpers.

Change Tracker:
    v1.0 — initial
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path


# ── Email ─────────────────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)


def fn_validate_email(email: str) -> bool:
    """
    Return True if the string looks like a valid email address.

    Uses a permissive RFC-5321-inspired regex — not exhaustive,
    but catches obvious typos and injection attempts.

    Args:
        email: The email string to check.

    Returns:
        True if valid, False otherwise.
    """
    return bool(_EMAIL_RE.match(email.strip()))


# ── Filename ──────────────────────────────────────────────────────────────────

_UNSAFE_FILENAME_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_MAX_FILENAME_LENGTH = 255


def fn_validate_filename(filename: str) -> bool:
    """
    Return True if the filename is safe to use on the filesystem.

    Checks:
        - Not empty
        - Does not contain path-traversal sequences
        - Does not contain OS-reserved characters
        - Length ≤ 255 characters

    Args:
        filename: The filename to validate (basename only, not a full path).

    Returns:
        True if safe, False otherwise.
    """
    if not filename or not filename.strip():
        return False
    if ".." in filename or "/" in filename or "\\" in filename:
        return False
    if _UNSAFE_FILENAME_RE.search(filename):
        return False
    if len(filename) > _MAX_FILENAME_LENGTH:
        return False
    return True


# ── String sanitisation ───────────────────────────────────────────────────────

def fn_sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Strip leading/trailing whitespace and truncate to max_length.

    Replaces null bytes which can cause issues in PostgreSQL TEXT columns.

    Args:
        value:      The raw string.
        max_length: Maximum allowed length (default 1000).

    Returns:
        Cleaned string.
    """
    cleaned = value.strip().replace("\x00", "")
    return cleaned[:max_length]


# ── UUID ──────────────────────────────────────────────────────────────────────

def fn_validate_uuid(value: str) -> bool:
    """
    Return True if value is a valid UUID (any version).

    Args:
        value: The string to test.

    Returns:
        True if valid UUID, False otherwise.
    """
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError):
        return False