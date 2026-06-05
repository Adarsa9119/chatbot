"""
pdf_utils.py — PDF text and image extraction helpers.

Depends on:
    pdfplumber  — text + table extraction
    PyMuPDF (fitz) — image extraction, page rendering

Change Tracker:
    v1.0 — initial
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, Optional

from config.logging_config import logger

try:
    import pdfplumber
except ImportError:  # pragma: no cover
    pdfplumber = None  # type: ignore

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    fitz = None  # type: ignore


def fn_extract_text_from_pdf(filepath: str | Path) -> str:
    """
    Extract all text from a PDF file using pdfplumber.

    Pages with no selectable text return an empty string for that page.
    Text from all pages is joined with double newlines.

    Args:
        filepath: Path to the PDF file.

    Returns:
        Full extracted text as a single string.

    Raises:
        RuntimeError: If pdfplumber is not installed.
        FileNotFoundError: If the file does not exist.
    """
    if pdfplumber is None:
        raise RuntimeError("pdfplumber is not installed. Run: pip install pdfplumber")

    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    pages_text: List[str] = []

    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages):
            try:
                text = page.extract_text() or ""
                pages_text.append(text)
            except Exception as e:
                logger.warning(f"Failed to extract text from page {i + 1} of {path}: {e}")
                pages_text.append("")

    full_text = "\n\n".join(pages_text)
    logger.debug(f"Extracted {len(full_text)} chars from {path.name}")
    return full_text


def fn_get_pdf_page_count(filepath: str | Path) -> int:
    """
    Return the number of pages in a PDF.

    Args:
        filepath: Path to the PDF file.

    Returns:
        Page count as an integer.

    Raises:
        RuntimeError: If neither pdfplumber nor fitz is available.
    """
    path = Path(filepath)

    if pdfplumber is not None:
        with pdfplumber.open(str(path)) as pdf:
            return len(pdf.pages)

    if fitz is not None:
        with fitz.open(str(path)) as doc:
            return doc.page_count

    raise RuntimeError("Install pdfplumber or PyMuPDF to count PDF pages.")


def fn_extract_images_from_pdf(
    filepath: str | Path,
    output_dir: str | Path,
    dpi: int = 150,
) -> List[Path]:
    """
    Render each PDF page as a PNG image and save to output_dir.

    Useful for scanned PDFs that need OCR processing.

    Args:
        filepath:   Path to the PDF file.
        output_dir: Directory where rendered images will be saved.
        dpi:        Rendering resolution (default 150 DPI).

    Returns:
        List of paths to the saved image files.

    Raises:
        RuntimeError: If PyMuPDF (fitz) is not installed.
        FileNotFoundError: If the PDF file does not exist.
    """
    if fitz is None:
        raise RuntimeError("PyMuPDF is not installed. Run: pip install PyMuPDF")

    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    saved_images: List[Path] = []
    mat = fitz.Matrix(dpi / 72, dpi / 72)  # scale factor

    with fitz.open(str(path)) as doc:
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=mat)
            img_path = out_dir / f"{path.stem}_page_{page_num + 1:04d}.png"
            pix.save(str(img_path))
            saved_images.append(img_path)
            logger.debug(f"Rendered page {page_num + 1} → {img_path}")

    logger.info(f"Extracted {len(saved_images)} images from {path.name}")
    return saved_images