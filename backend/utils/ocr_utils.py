"""
ocr_utils.py — OCR helpers using Tesseract via pytesseract.

Depends on:
    pytesseract  — Python wrapper for Tesseract OCR
    Pillow       — Image loading
    pdfplumber   — Scanned PDF detection

Change Tracker:
    v1.0 — initial
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from config.logging_config import logger

try:
    import pytesseract
    from PIL import Image
except ImportError:  # pragma: no cover
    pytesseract = None  # type: ignore
    Image = None  # type: ignore

try:
    import pdfplumber
except ImportError:  # pragma: no cover
    pdfplumber = None  # type: ignore

# Minimum average character count per page to consider a PDF "text-based".
_SCANNED_THRESHOLD_CHARS_PER_PAGE = 50


def fn_ocr_image(image_path: str | Path, lang: str = "eng") -> str:
    """
    Run Tesseract OCR on an image file and return the extracted text.

    Args:
        image_path: Path to the image file (PNG, JPEG, TIFF, etc.).
        lang:       Tesseract language code (default: 'eng').

    Returns:
        Extracted text as a string.

    Raises:
        RuntimeError: If pytesseract / Pillow are not installed.
        FileNotFoundError: If the image file does not exist.
    """
    if pytesseract is None or Image is None:
        raise RuntimeError(
            "pytesseract and Pillow are required. "
            "Run: pip install pytesseract Pillow"
        )

    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    try:
        img = Image.open(str(path))
        text = pytesseract.image_to_string(img, lang=lang)
        logger.debug(f"OCR extracted {len(text)} chars from {path.name}")
        return text
    except Exception as e:
        logger.error(f"OCR failed for {path.name}: {e}")
        raise


def fn_ocr_pdf_page(image_path: str | Path, lang: str = "eng") -> str:
    """
    OCR a pre-rendered PDF page image.

    This is an alias for fn_ocr_image, provided for semantic clarity when
    the caller has rendered a PDF page to a PNG and wants to OCR it.

    Args:
        image_path: Path to the rendered page image.
        lang:       Tesseract language code.

    Returns:
        Extracted text string.
    """
    return fn_ocr_image(image_path, lang=lang)


def fn_is_scanned_pdf(
    filepath: str | Path,
    threshold: int = _SCANNED_THRESHOLD_CHARS_PER_PAGE,
) -> bool:
    """
    Heuristically determine whether a PDF is scanned (image-only) or text-based.

    Strategy: extract text from up to the first 5 pages; if the average
    character count per page is below `threshold`, treat the PDF as scanned.

    Args:
        filepath:  Path to the PDF file.
        threshold: Min avg chars/page to consider text-based (default 50).

    Returns:
        True  → PDF appears to be scanned (OCR needed).
        False → PDF has selectable text.

    Raises:
        RuntimeError: If pdfplumber is not installed.
    """
    if pdfplumber is None:
        raise RuntimeError("pdfplumber is not installed. Run: pip install pdfplumber")

    path = Path(filepath)
    sample_pages = 5
    total_chars = 0
    pages_checked = 0

    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages[:sample_pages]:
            text = page.extract_text() or ""
            total_chars += len(text)
            pages_checked += 1

    if pages_checked == 0:
        return True  # Empty PDF — treat as scanned

    avg = total_chars / pages_checked
    is_scanned = avg < threshold
    logger.debug(
        f"{path.name}: avg_chars_per_page={avg:.1f}, "
        f"threshold={threshold}, is_scanned={is_scanned}"
    )
    return is_scanned