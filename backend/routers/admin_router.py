"""
admin_router.py — Admin-only endpoints: documents, users, dashboard stats.
Change Tracker:
  v1.0 — initial
"""

from fastapi import APIRouter, Depends, File, Form, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional

from config.database import fn_get_db
from config.logging_config import logger
from middleware.auth_middleware import fn_require_admin
from services.document_service import DocumentService
from schemas.document_schema import (
    DocumentResponse, DocumentListResponse,
    DocumentStatusResponse, DocumentDeleteResponse, DocumentReprocessResponse
)
from schemas.user_schema import UserListResponse
from database.crud_users import fn_get_all_users, fn_count_users
from database.crud_documents import fn_count_documents, fn_get_all_documents
from database.crud_sessions import fn_count_sessions
from database.crud_chat import fn_count_messages
from database.crud_audit_logs import fn_create_audit_log
from background_tasks.process_document_task import fn_process_document_task


router = APIRouter(prefix="/admin", tags=["Admin"])
var_doc_service = DocumentService()


@router.get("/dashboard")
def fn_admin_dashboard(
    db: Session = Depends(fn_get_db),
    admin=Depends(fn_require_admin),
):
    """GET /api/v1/admin/dashboard — statistics for admin dashboard."""
    return {
        "total_documents": fn_count_documents(db),
        "total_users": fn_count_users(db),
        "total_sessions": fn_count_sessions(db),
        "total_messages": fn_count_messages(db),
        "recent_documents": [
            {
                "doc_id": d.doc_id,
                "title": d.title,
                "status": d.status,
                "created_at": d.created_at,
            }
            for d in fn_get_all_documents(db, limit=5)
        ],
    }


@router.post("/documents", response_model=DocumentResponse, status_code=201)
async def fn_upload_document(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(fn_get_db),
    admin=Depends(fn_require_admin),
):
    """POST /api/v1/admin/documents — upload a PDF and start processing."""
    var_doc = await var_doc_service.fn_save_upload(
        db=db,
        file=file,
        title=title,
        description=description,
        uploaded_by=admin.user_id,
    )

    # Queue background processing task
    background_tasks.add_task(fn_process_document_task, var_doc.doc_id)

    fn_create_audit_log(
        db, action="document_upload",
        user_id=admin.user_id,
        resource_type="document",
        resource_id=var_doc.doc_id,
        details={"title": title},
    )

    logger.info(f"Upload queued: doc_id={var_doc.doc_id} by admin={admin.user_id}")
    return DocumentResponse.model_validate(var_doc)


@router.get("/documents", response_model=DocumentListResponse)
def fn_list_documents(
    db: Session = Depends(fn_get_db),
    admin=Depends(fn_require_admin),
):
    """GET /api/v1/admin/documents — list all documents."""
    var_docs = var_doc_service.fn_list_documents(db)
    return DocumentListResponse(
        total=len(var_docs),
        documents=[DocumentResponse.model_validate(d) for d in var_docs],
    )


@router.get("/documents/{doc_id}/status", response_model=DocumentStatusResponse)
def fn_get_document_status(
    doc_id: int,
    db: Session = Depends(fn_get_db),
    admin=Depends(fn_require_admin),
):
    """GET /api/v1/admin/documents/{doc_id}/status — poll processing status."""
    var_doc = var_doc_service.fn_get_document(db, doc_id)
    return DocumentStatusResponse(
        doc_id=var_doc.doc_id,
        status=var_doc.status,
        error_message=var_doc.error_message,
    )


@router.delete("/documents/{doc_id}", response_model=DocumentDeleteResponse)
def fn_delete_document(
    doc_id: int,
    db: Session = Depends(fn_get_db),
    admin=Depends(fn_require_admin),
):
    """DELETE /api/v1/admin/documents/{doc_id} — delete document and all chunks."""
    var_doc_service.fn_delete_document(db, doc_id)
    fn_create_audit_log(
        db, action="document_delete",
        user_id=admin.user_id,
        resource_type="document",
        resource_id=doc_id,
    )
    return DocumentDeleteResponse()


@router.post("/documents/{doc_id}/reprocess", response_model=DocumentReprocessResponse)
def fn_reprocess_document(
    doc_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(fn_get_db),
    admin=Depends(fn_require_admin),
):
    """POST /api/v1/admin/documents/{doc_id}/reprocess — re-run processing pipeline."""
    var_doc_service.fn_mark_reprocess(db, doc_id)
    background_tasks.add_task(fn_process_document_task, doc_id)
    fn_create_audit_log(
        db, action="document_reprocess",
        user_id=admin.user_id,
        resource_type="document",
        resource_id=doc_id,
    )
    return DocumentReprocessResponse(doc_id=doc_id)


@router.get("/users", response_model=UserListResponse)
def fn_list_users(
    db: Session = Depends(fn_get_db),
    admin=Depends(fn_require_admin),
):
    """GET /api/v1/admin/users — list all registered users."""
    from schemas.user_schema import UserResponse
    var_users = fn_get_all_users(db)
    return UserListResponse(
        total=len(var_users),
        users=[UserResponse.model_validate(u) for u in var_users],
    )