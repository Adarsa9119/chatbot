"""
crud_documents.py — Database operations for the documents table.
Change Tracker:
  v1.0 — initial
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from models.document_model import DocumentsModel
from config.logging_config import logger


def fn_create_document(
    db: Session,
    title: str,
    file_path: str,
    uploaded_by: int,
    description: Optional[str] = None,
    file_size_kb: Optional[int] = None,
) -> DocumentsModel:
    """Insert a new document record with status='processing'."""
    try:
        var_doc = DocumentsModel(
            title=title,
            description=description,
            file_path=file_path,
            file_size_kb=file_size_kb,
            uploaded_by=uploaded_by,
            status="processing",
        )
        db.add(var_doc)
        db.commit()
        db.refresh(var_doc)
        logger.info(f"Document created: id={var_doc.doc_id} title={title}")
        return var_doc
    except Exception as e:
        db.rollback()
        logger.error(f"fn_create_document error: {e}")
        raise


def fn_get_document_by_id(db: Session, doc_id: int) -> Optional[DocumentsModel]:
    """Fetch a document by primary key."""
    try:
        return db.query(DocumentsModel).filter(DocumentsModel.doc_id == doc_id).first()
    except Exception as e:
        logger.error(f"fn_get_document_by_id error: {e}")
        return None


def fn_get_all_documents(db: Session, skip: int = 0, limit: int = 100) -> List[DocumentsModel]:
    """Admin: list all documents."""
    try:
        return (
            db.query(DocumentsModel)
            .order_by(DocumentsModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    except Exception as e:
        logger.error(f"fn_get_all_documents error: {e}")
        return []


def fn_get_ready_documents(db: Session) -> List[DocumentsModel]:
    """User: list all documents with status='ready'."""
    try:
        return (
            db.query(DocumentsModel)
            .filter(DocumentsModel.status == "ready")
            .order_by(DocumentsModel.created_at.desc())
            .all()
        )
    except Exception as e:
        logger.error(f"fn_get_ready_documents error: {e}")
        return []


def fn_update_document_status(
    db: Session,
    doc_id: int,
    status: str,
    ocr_required: Optional[bool] = None,
    error_message: Optional[str] = None,
) -> Optional[DocumentsModel]:
    """Update processing status of a document."""
    try:
        var_doc = fn_get_document_by_id(db, doc_id)
        if not var_doc:
            return None
        var_doc.status = status
        if ocr_required is not None:
            var_doc.ocr_required = ocr_required
        if error_message is not None:
            var_doc.error_message = error_message
        db.commit()
        db.refresh(var_doc)
        return var_doc
    except Exception as e:
        db.rollback()
        logger.error(f"fn_update_document_status error: {e}")
        raise


def fn_delete_document(db: Session, doc_id: int) -> bool:
    """Delete a document and cascade to its chunks."""
    try:
        var_doc = fn_get_document_by_id(db, doc_id)
        if not var_doc:
            return False
        db.delete(var_doc)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"fn_delete_document error: {e}")
        raise


def fn_count_documents(db: Session) -> int:
    """Total document count."""
    try:
        return db.query(func.count(DocumentsModel.doc_id)).scalar() or 0
    except Exception as e:
        logger.error(f"fn_count_documents error: {e}")
        return 0