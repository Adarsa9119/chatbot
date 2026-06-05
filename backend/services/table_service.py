"""
table_service.py — PDF table extraction and conversion to structured text.
Used by the document processing pipeline to handle tables separately from body text.
Change Tracker:
  v1.0 — initial
"""

from typing import List, Optional
from config.logging_config import logger


class TableService:
    """
    Extracts and formats tables from PDF pages.
    Tables are converted to pipe-separated text and Markdown
    so they can be meaningfully embedded and searched.
    """

    def fn_extract_tables_from_page(self, pdf_page) -> List[dict]:
        """
        Extract all tables from a single pdfplumber page object.
        Returns list of { table_index, rows, formatted_text }

        Args:
            pdf_page: a pdfplumber Page object
        """
        var_tables = []
        try:
            var_raw_tables = pdf_page.extract_tables()
            if not var_raw_tables:
                return []

            for var_table_idx, var_table in enumerate(var_raw_tables):
                if not var_table:
                    continue

                var_cleaned_rows = self.help_fn_clean_table_rows(var_table)
                if not var_cleaned_rows:
                    continue

                var_formatted = self.fn_format_table_as_markdown(var_cleaned_rows)
                var_pipe_text = self.fn_format_table_as_pipe(var_cleaned_rows)

                var_tables.append({
                    "table_index": var_table_idx,
                    "rows": var_cleaned_rows,
                    "formatted_markdown": var_formatted,
                    "formatted_pipe": var_pipe_text,
                    "row_count": len(var_cleaned_rows),
                    "col_count": len(var_cleaned_rows[0]) if var_cleaned_rows else 0,
                })

        except Exception as e:
            logger.warning(f"fn_extract_tables_from_page error: {e}")

        return var_tables

    def help_fn_clean_table_rows(self, raw_table: list) -> List[List[str]]:
        """
        Sanitise raw table cells:
        - Strip whitespace
        - Replace None with empty string
        - Remove fully empty rows
        """
        var_cleaned = []
        for var_row in raw_table:
            if not var_row:
                continue
            var_clean_row = [str(cell).strip() if cell is not None else "" for cell in var_row]
            # Skip rows where every cell is empty
            if any(var_clean_row):
                var_cleaned.append(var_clean_row)
        return var_cleaned

    def fn_format_table_as_markdown(self, rows: List[List[str]]) -> str:
        """
        Convert cleaned rows to a Markdown table.
        First row is treated as the header.

        Example output:
        | Column A | Column B |
        |----------|----------|
        | value1   | value2   |
        """
        if not rows:
            return ""

        var_header = rows[0]
        var_separator = ["-" * max(len(cell), 3) for cell in var_header]
        var_data_rows = rows[1:]

        var_lines = []
        var_lines.append("| " + " | ".join(var_header) + " |")
        var_lines.append("| " + " | ".join(var_separator) + " |")

        for var_row in var_data_rows:
            # Pad row to match header width
            while len(var_row) < len(var_header):
                var_row.append("")
            var_lines.append("| " + " | ".join(var_row[: len(var_header)]) + " |")

        return "\n".join(var_lines)

    def fn_format_table_as_pipe(self, rows: List[List[str]]) -> str:
        """
        Convert cleaned rows to pipe-separated text.
        More compact than Markdown; used for embedding where formatting is noise.

        Example: Cell1 | Cell2 | Cell3
        """
        var_lines = []
        for var_row in rows:
            var_lines.append(" | ".join(var_row))
        return "\n".join(var_lines)

    def fn_tables_to_chunk_text(
        self,
        tables: List[dict],
        page_num: Optional[int] = None,
    ) -> str:
        """
        Convert all tables on a page to a single embeddable text block.
        Each table is preceded by a [TABLE N] marker.
        Used when merging table content with body text for chunking.
        """
        if not tables:
            return ""

        var_parts = []
        var_page_label = f" (Page {page_num})" if page_num else ""

        for var_table in tables:
            var_label = f"[TABLE {var_table['table_index'] + 1}{var_page_label}]"
            var_parts.append(f"{var_label}\n{var_table['formatted_pipe']}")

        return "\n\n".join(var_parts)

    def fn_extract_all_tables_from_pdf(self, pdf_path: str) -> List[dict]:
        """
        Extract all tables from all pages of a PDF.
        Returns list of { page_num, table_index, ... } dicts.
        Only called when you need standalone table extraction (not via ocr_service).
        """
        try:
            import pdfplumber
        except ImportError:
            logger.error("pdfplumber not installed — cannot extract tables")
            return []

        var_all_tables = []
        try:
            with pdfplumber.open(pdf_path) as var_pdf:
                for var_page_num, var_page in enumerate(var_pdf.pages, 1):
                    var_page_tables = self.fn_extract_tables_from_page(var_page)
                    for var_table in var_page_tables:
                        var_table["page_num"] = var_page_num
                        var_all_tables.append(var_table)

            logger.info(
                f"Extracted {len(var_all_tables)} tables from {pdf_path}"
            )
        except Exception as e:
            logger.error(f"fn_extract_all_tables_from_pdf error: {e}")

        return var_all_tables


# ── Singleton ────────────────────────────────────────────────
table_service = TableService()