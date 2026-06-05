"""
document_controller.py — Controller for all document management operations.
Coordinates: document_service, audit_service, background processing tasks.
Change Tracker:
  v1.0 — initial
"""

from fastapi import BackgroundTasks, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session
from typing import Optional, List

from config.logging_config import logger
from services.document_service import DocumentService
from services.audit_service import audit_service, AuditAction
from database.crud_documents import (
    fn_get_all_documents,
    fn_get_ready_documents,
    fn_count_documents,
    fn_get_document_by_id,
)
from background_tasks.process_document_task import fn_process_document_task
from schemas.document_schema import (
    DocumentResponse,
    DocumentListResponse,
    DocumentStatusResponse,
    DocumentDeleteResponse,
    DocumentReprocessResponse,
)

_doc_service = DocumentService()


class DocumentController:
    """
    Handles all document-related request logic:
      fn_handle_upload          — validate + save file, queue background processing
      fn_handle_list_all        — admin: all documents with stats
      fn_handle_list_ready      — user: only 'ready' documents
      fn_handle_get_status      — poll document processing status
      fn_handle_delete          — delete document, file, and chunks
      fn_handle_reprocess       — reset and re-run processing pipeline
      fn_handle_get_document    — fetch single document by ID
    """

    # ────────────────────────────────────────────────────────
    # Upload
    # ────────────────────────────────────────────────────────

    async def fn_handle_upload(
        self,
        db: Session,
        request: Request,
        background_tasks: BackgroundTasks,
        file: UploadFile,
        title: str,
        description: Optional[str],
        uploaded_by_user_id: int,
    ) -> DocumentResponse:
        """
        Handle PDF upload:
          1. Validate file type and size (in document_service)
          2. Save file to uploads/documents/
          3. Create document DB record (status=processing)
          4. Queue background processing task
          5. Audit log

        Returns the created document immediately (processing happens async).
        Frontend polls /status to track progress.
        """
        # ── Validate title ───────────────────────────────────
        var_title = title.strip()
        if not var_title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document title cannot be empty",
            )

        # ── Save upload ──────────────────────────────────────
        var_doc = await _doc_service.fn_save_upload(
            db=db,
            file=file,
            title=var_title,
            description=description,
            uploaded_by=uploaded_by_user_id,
        )

        # ── Queue background task ────────────────────────────
        background_tasks.add_task(fn_process_document_task, var_doc.doc_id)

        # ── Audit ────────────────────────────────────────────
        audit_service.fn_log_document_upload(
            db,
            user_id=uploaded_by_user_id,
            doc_id=var_doc.doc_id,
            doc_title=var_title,
            request=request,
        )

        logger.info(
            f"Document uploaded: doc_id={var_doc.doc_id} title='{var_title}' "
            f"by user_id={uploaded_by_user_id}"
        )

        return DocumentResponse.model_validate(var_doc)

    # ────────────────────────────────────────────────────────
    # List (admin — all)
    # ────────────────────────────────────────────────────────

    def fn_handle_list_all(self, db: Session) -> DocumentListResponse:
        """
        Admin: return all documents regardless of status.
        Includes processing, ready, and failed documents.
        """
        var_docs = fn_get_all_documents(db)
        var_total = fn_count_documents(db)

        logger.debug(f"Admin document list: total={var_total}")
        return DocumentListResponse(
            total=var_total,
            documents=[DocumentResponse.model_validate(d) for d in var_docs],
        )

    # ────────────────────────────────────────────────────────
    # List (user — ready only)
    # ────────────────────────────────────────────────────────

    def fn_handle_list_ready(self, db: Session) -> List[DocumentResponse]:
        """
        User: return only documents with status='ready'.
        Users should never see processing or failed documents.
        """
        var_docs = fn_get_ready_documents(db)
        logger.debug(f"User ready documents: count={len(var_docs)}")
        return [DocumentResponse.model_validate(d) for d in var_docs]

    # ────────────────────────────────────────────────────────
    # Get single document
    # ────────────────────────────────────────────────────────

    def fn_handle_get_document(self, db: Session, doc_id: int) -> DocumentResponse:
        """Fetch a single document by ID. Raises 404 if not found."""
        var_doc = _doc_service.fn_get_document(db, doc_id)
        return DocumentResponse.model_validate(var_doc)

    # ────────────────────────────────────────────────────────
    # Status poll
    # ────────────────────────────────────────────────────────

    def fn_handle_get_status(
        self,
        db: Session,
        doc_id: int,
    ) -> DocumentStatusResponse:
        """
        Poll document processing status.
        Frontend calls this every few seconds after upload
        until status = 'ready' or 'failed'.
        """
        var_doc = _doc_service.fn_get_document(db, doc_id)

        var_response = DocumentStatusResponse(
            doc_id=var_doc.doc_id,
            status=var_doc.status,
            error_message=var_doc.error_message,
        )

        logger.debug(f"Status poll: doc_id={doc_id} status={var_doc.status}")
        return var_response

    # ────────────────────────────────────────────────────────
    # Delete
    # ────────────────────────────────────────────────────────

    def fn_handle_delete(
        self,
        db: Session,
        request: Request,
        doc_id: int,
        deleted_by_user_id: int,
    ) -> DocumentDeleteResponse:
        """
        Delete a document:
          1. Verify document exists
          2. Delete physical file from disk
          3. Delete DB record (cascades to chunks via FK)
          4. Audit log
        """
        # Verify exists before proceeding
        var_doc = fn_get_document_by_id(db, doc_id)
        if not var_doc:
            raise HTTPException(status_code=404, detail="Document not found")

        var_title = var_doc.title  # capture before delete

        # Service handles file + DB delete
        _doc_service.fn_delete_document(db, doc_id)

        # ── Audit ────────────────────────────────────────────
        audit_service.fn_log(
            db,
            action=AuditAction.DOCUMENT_DELETE,
            user_id=deleted_by_user_id,
            resource_type="document",
            resource_id=doc_id,
            details={"title": var_title},
            request=request,
        )

        logger.info(
            f"Document deleted: doc_id={doc_id} title='{var_title}' "
            f"by user_id={deleted_by_user_id}"
        )
        return DocumentDeleteResponse()

    # ────────────────────────────────────────────────────────
    # Reprocess
    # ────────────────────────────────────────────────────────

    def fn_handle_reprocess(
        self,
        db: Session,
        request: Request,
        background_tasks: BackgroundTasks,
        doc_id: int,
        reprocessed_by_user_id: int,
    ) -> DocumentReprocessResponse:
        """
        Re-run the document processing pipeline:
          1. Delete all existing chunks for the document
          2. Reset status to 'processing'
          3. Queue background processing task again
          4. Audit log

        Used when: initial processing failed, model was updated,
        or admin wants to re-embed with new chunk settings.
        """
        # Verify exists
        var_doc = fn_get_document_by_id(db, doc_id)
        if not var_doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Reset status + delete old chunks
        _doc_service.fn_mark_reprocess(db, doc_id)

        # Queue fresh processing
        background_tasks.add_task(fn_process_document_task, doc_id)

        # ── Audit ────────────────────────────────────────────
        audit_service.fn_log(
            db,
            action=AuditAction.DOCUMENT_REPROCESS,
            user_id=reprocessed_by_user_id,
            resource_type="document",
            resource_id=doc_id,
            details={"title": var_doc.title},
            request=request,
        )

        logger.info(
            f"Document reprocess queued: doc_id={doc_id} "
            f"by user_id={reprocessed_by_user_id}"
        )
        return DocumentReprocessResponse(doc_id=doc_id)


# ── Singleton ────────────────────────────────────────────────
document_controller = DocumentController()