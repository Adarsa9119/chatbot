"""
table_utils.py — PDF table extraction and Markdown serialisation.

Depends on:
    pdfplumber — table detection

Change Tracker:
    v1.0 — initial
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from config.logging_config import logger

try:
    import pdfplumber
except ImportError:  # pragma: no cover
    pdfplumber = None  # type: ignore


# ── Type alias ────────────────────────────────────────────────────────────────

# A table is a list of rows; each row is a list of cell strings.
Table = List[List[Optional[str]]]


def fn_extract_tables_from_pdf(filepath: str | Path) -> List[Table]:
    """
    Extract all tables from every page of a PDF.

    Cells with no content are returned as empty strings (None → "").

    Args:
        filepath: Path to the PDF file.

    Returns:
        A list of tables; each table is a list-of-lists of cell strings.
        Returns an empty list if no tables are found.

    Raises:
        RuntimeError: If pdfplumber is not installed.
        FileNotFoundError: If the file does not exist.
    """
    if pdfplumber is None:
        raise RuntimeError("pdfplumber is not installed. Run: pip install pdfplumber")

    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    all_tables: List[Table] = []

    with pdfplumber.open(str(path)) as pdf:
        for page_num, page in enumerate(pdf.pages):
            try:
                tables = page.extract_tables()
                for table in tables:
                    # Normalise: replace None cells with ""
                    normalised = [
                        [cell if cell is not None else "" for cell in row]
                        for row in table
                    ]
                    all_tables.append(normalised)
            except Exception as e:
                logger.warning(
                    f"Table extraction failed on page {page_num + 1} of {path.name}: {e}"
                )

    logger.debug(f"Extracted {len(all_tables)} tables from {path.name}")
    return all_tables


def fn_tables_to_markdown(tables: List[Table]) -> str:
    """
    Convert a list of tables (as returned by fn_extract_tables_from_pdf)
    to GitHub-flavoured Markdown table syntax.

    The first row of each table is treated as the header row.
    Tables are separated by a blank line.

    Args:
        tables: List of tables (each a list-of-rows of cell strings).

    Returns:
        A Markdown string with all tables formatted.
    """
    if not tables:
        return ""

    md_blocks: List[str] = []

    for table in tables:
        if not table:
            continue

        lines: List[str] = []
        header = table[0]
        data_rows = table[1:]

        # Header row
        lines.append("| " + " | ".join(str(cell) for cell in header) + " |")
        # Separator
        lines.append("| " + " | ".join("---" for _ in header) + " |")
        # Data rows
        for row in data_rows:
            # Pad or truncate row to match header width
            padded = list(row) + [""] * (len(header) - len(row))
            padded = padded[: len(header)]
            lines.append("| " + " | ".join(str(cell) for cell in padded) + " |")

        md_blocks.append("\n".join(lines))

    return "\n\n".join(md_blocks)