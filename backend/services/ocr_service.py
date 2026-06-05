"""
ocr_service.py — PDF text extraction: pdfplumber (text PDFs) + pytesseract (scanned).
FIXED: Set Tesseract and Poppler paths at module level for Windows.
Change Tracker:
  v1.0 — initial
"""

import os
import pytesseract
from pathlib import Path
from typing import Optional
from config.settings import settings
from config.logging_config import logger

# ── WINDOWS FIX: set tool paths at module level ──────────────
# MUST happen before any pytesseract or pdf2image call
pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH
POPPLER_PATH = settings.POPPLER_PATH

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from pdf2image import convert_from_path
except ImportError:
    convert_from_path = None


class OcrService:
    """
    Extracts text from PDF files.
    Strategy: try pdfplumber first; fall back to OCR if text too short.
    """

    def help_fn_extract_text_pdfplumber(self, pdf_path: str) -> str:
        """
        Extract text from a text-based PDF using pdfplumber.
        Also extracts tables as pipe-separated text.
        """
        if pdfplumber is None:
            logger.warning("pdfplumber not installed")
            return ""
        try:
            var_text_parts = []
            with pdfplumber.open(pdf_path) as var_pdf:
                for var_page_num, var_page in enumerate(var_pdf.pages, 1):
                    # Extract regular text
                    var_page_text = var_page.extract_text() or ""

                    # Extract tables
                    var_tables = var_page.extract_tables()
                    var_table_text = ""
                    for var_table in var_tables:
                        for var_row in var_table:
                            var_clean_row = [str(cell or "").strip() for cell in var_row]
                            var_table_text += " | ".join(var_clean_row) + "\n"

                    var_combined = var_page_text
                    if var_table_text:
                        var_combined += "\n[TABLE]\n" + var_table_text

                    if var_combined.strip():
                        var_text_parts.append(f"[PAGE {var_page_num}]\n{var_combined}")

            return "\n\n".join(var_text_parts).strip()
        except Exception as e:
            logger.error(f"help_fn_extract_text_pdfplumber error: {e}")
            return ""

    def help_fn_extract_text_ocr(self, pdf_path: str) -> str:
        """
        Extract text from a scanned/image PDF using pytesseract.
        FIXED: Must pass poppler_path on Windows.
        """
        if convert_from_path is None:
            logger.warning("pdf2image not installed")
            return ""
        try:
            var_images = convert_from_path(
                pdf_path,
                poppler_path=POPPLER_PATH,  # REQUIRED on Windows
                dpi=300,
            )
            var_pages = []
            for var_idx, var_img in enumerate(var_images, 1):
                var_text = pytesseract.image_to_string(var_img)
                if var_text.strip():
                    var_pages.append(f"[PAGE {var_idx}]\n{var_text}")
            return "\n\n".join(var_pages).strip()
        except Exception as e:
            logger.error(f"help_fn_extract_text_ocr error: {e}")
            return ""

    def fn_extract_text(self, pdf_path: str) -> tuple[str, bool]:
        """
        Main extraction function.
        Returns (extracted_text, ocr_used_flag).
        Falls back to OCR if text length < MIN_TEXT_LENGTH.
        """
        var_text = self.help_fn_extract_text_pdfplumber(pdf_path)
        var_ocr_used = False

        if len(var_text.strip()) < settings.MIN_TEXT_LENGTH:
            logger.info(f"Short text ({len(var_text)} chars) — falling back to OCR: {pdf_path}")
            var_text = self.help_fn_extract_text_ocr(pdf_path)
            var_ocr_used = True

        logger.info(
            f"Extracted {len(var_text)} chars from {pdf_path} "
            f"(ocr={'yes' if var_ocr_used else 'no'})"
        )
        return var_text, var_ocr_used