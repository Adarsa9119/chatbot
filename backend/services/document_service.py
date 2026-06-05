"""
document_service.py — Business logic for document management.
Change Tracker:
  v1.0 — initial
"""

import os
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from typing import Optional, List

from config.settings import settings
from config.logging_config import logger
from database.crud_documents import (
    fn_create_document, fn_get_document_by_id,
    fn_get_all_documents, fn_get_ready_documents,
    fn_update_document_status, fn_delete_document,
)
from database.crud_chunks import fn_delete_chunks_by_doc
from models.document_model import DocumentsModel


# ── Constants ────────────────────────────────────────────────
MAX_FILE_SIZE_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"application/pdf"}


class DocumentService:
    """Handles document upload, status, delete, and reprocess logic."""

    async def fn_save_upload(
        self,
        db: Session,
        file: UploadFile,
        title: str,
        description: Optional[str],
        uploaded_by: int,
    ) -> DocumentsModel:
        """
        Validate and save an uploaded PDF file.
        ADDED: File type and size validation (not in original spec).
        Returns the created document record.
        """
        # ── Validate file type ───────────────────────────────
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # ── Read and validate file size ──────────────────────
        var_contents = await file.read()
        var_size_bytes = len(var_contents)
        if var_size_bytes > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit",
            )
        await file.seek(0)  # Reset stream

        # ── Ensure upload directory exists ───────────────────
        var_upload_dir = Path(settings.UPLOAD_DIR)
        var_upload_dir.mkdir(parents=True, exist_ok=True)

        # ── Save file to disk ────────────────────────────────
        # Use pathlib.Path — never hardcode slashes (Windows fix)
        var_filename = f"{uploaded_by}_{file.filename}"
        var_file_path = var_upload_dir / var_filename

        with open(var_file_path, "wb") as var_f:
            var_f.write(var_contents)

        var_size_kb = var_size_bytes // 1024

        # ── Create DB record ─────────────────────────────────
        var_doc = fn_create_document(
            db=db,
            title=title,
            file_path=str(var_file_path),
            uploaded_by=uploaded_by,
            description=description,
            file_size_kb=var_size_kb,
        )

        logger.info(f"File saved: {var_file_path} ({var_size_kb} KB) doc_id={var_doc.doc_id}")
        return var_doc

    def fn_get_document(self, db: Session, doc_id: int) -> DocumentsModel:
        """Get document or raise 404."""
        var_doc = fn_get_document_by_id(db, doc_id)
        if not var_doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return var_doc

    def fn_list_documents(self, db: Session) -> List[DocumentsModel]:
        """Admin: all documents."""
        return fn_get_all_documents(db)

    def fn_list_ready_documents(self, db: Session) -> List[DocumentsModel]:
        """User: only ready documents."""
        return fn_get_ready_documents(db)

    def fn_delete_document(self, db: Session, doc_id: int) -> bool:
        """Delete document, its chunks, and the physical file."""
        var_doc = fn_get_document_by_id(db, doc_id)
        if not var_doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete physical file
        try:
            var_path = Path(var_doc.file_path)
            if var_path.exists():
                var_path.unlink()
        except Exception as e:
            logger.warning(f"Could not delete file {var_doc.file_path}: {e}")

        # DB delete (cascades to chunks)
        fn_delete_document(db, doc_id)
        logger.info(f"Document deleted: doc_id={doc_id}")
        return True

    def fn_mark_reprocess(self, db: Session, doc_id: int) -> DocumentsModel:
        """Reset document status to 'processing' for reprocessing."""
        var_doc = fn_get_document_by_id(db, doc_id)
        if not var_doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete existing chunks before reprocessing
        fn_delete_chunks_by_doc(db, doc_id)
        fn_update_document_status(db, doc_id, "processing", error_message=None)
        var_doc = fn_get_document_by_id(db, doc_id)
        return var_doc