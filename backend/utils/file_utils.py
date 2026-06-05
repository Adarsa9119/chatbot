"""
file_utils.py — Filesystem helpers for upload management.

Change Tracker:
    v1.0 — initial
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Optional

from config.logging_config import logger

# ── Allowed MIME types / extensions ──────────────────────────────────────────

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/tiff",
    "image/bmp",
    "image/webp",
}


def fn_allowed_file(filename: str) -> bool:
    """
    Return True if the file extension is in the allowed set.

    Args:
        filename: Original filename from upload.

    Returns:
        True if allowed, False otherwise.
    """
    ext = fn_get_file_extension(filename)
    return ext in ALLOWED_EXTENSIONS


def fn_get_file_extension(filename: str) -> str:
    """
    Return the lowercase file extension including the dot (e.g. '.pdf').

    Args:
        filename: Any filename string.

    Returns:
        Lowercase extension string or empty string if none.
    """
    return Path(filename).suffix.lower()


def fn_generate_unique_filename(original_filename: str) -> str:
    """
    Generate a UUID-based unique filename preserving the original extension.

    Example:
        'my doc.pdf'  →  'a3f2c1d0-...-4e5b.pdf'

    Args:
        original_filename: The original uploaded filename.

    Returns:
        A unique filename safe for use on the filesystem.
    """
    ext = fn_get_file_extension(original_filename)
    return f"{uuid.uuid4()}{ext}"


def fn_get_file_size_mb(filepath: str | Path) -> float:
    """
    Return the file size in megabytes, rounded to 2 decimal places.

    Args:
        filepath: Path to the file.

    Returns:
        File size in MB.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    return round(path.stat().st_size / (1024 * 1024), 2)


def fn_ensure_dir(directory: str | Path) -> Path:
    """
    Create the directory (and any parents) if it does not already exist.

    Args:
        directory: Target directory path.

    Returns:
        The resolved Path object.
    """
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


def fn_delete_file(filepath: str | Path, silent: bool = True) -> bool:
    """
    Delete a file from the filesystem.

    Args:
        filepath: Path to the file to delete.
        silent:   If True, log a warning instead of raising on missing files.

    Returns:
        True if deleted, False if not found (when silent=True).

    Raises:
        FileNotFoundError: If file does not exist and silent=False.
    """
    path = Path(filepath)
    try:
        path.unlink()
        logger.debug(f"Deleted file: {path}")
        return True
    except FileNotFoundError:
        if silent:
            logger.warning(f"File not found for deletion: {path}")
            return False
        raise
    except Exception as e:
        logger.error(f"Error deleting file {path}: {e}")
        raise


def fn_move_file(
    src: str | Path,
    dst_dir: str | Path,
    new_name: Optional[str] = None,
) -> Path:
    """
    Move a file to a destination directory, optionally renaming it.

    Args:
        src:      Source file path.
        dst_dir:  Destination directory (created if missing).
        new_name: Optional new filename; defaults to the original name.

    Returns:
        The full destination path.

    Raises:
        FileNotFoundError: If the source file does not exist.
    """
    src_path = Path(src)
    if not src_path.exists():
        raise FileNotFoundError(f"Source file not found: {src_path}")

    dst_directory = fn_ensure_dir(dst_dir)
    filename = new_name or src_path.name
    dst_path = dst_directory / filename

    shutil.move(str(src_path), str(dst_path))
    logger.debug(f"Moved file: {src_path} → {dst_path}")
    return dst_path