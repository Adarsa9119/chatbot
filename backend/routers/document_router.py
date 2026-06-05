"""
document_router.py — User-facing document endpoints.
Authenticated users can list and view ready documents.
Admin upload/delete is in admin_router.py.

Change Tracker:
v1.0 — initial
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config.database import fn_get_db
from middleware.auth_middleware import fn_get_current_user
from services.document_service import DocumentService
from schemas.document_schema import DocumentResponse, DocumentListResponse

router = APIRouter(prefix="/documents", tags=["Documents"])
var_doc_service = DocumentService()


@router.get("", response_model=DocumentListResponse)
def fn_list_ready_documents(
    db: Session = Depends(fn_get_db),
    current_user=Depends(fn_get_current_user),
):
    """
    GET /api/v1/documents — list all documents with status='ready'.
    Used by the chat UI to populate the document selector.
    Both admin and regular users can access this endpoint.
    """
    var_docs = var_doc_service.fn_list_ready_documents(db)
    return DocumentListResponse(
        total=len(var_docs),
        documents=[DocumentResponse.model_validate(d) for d in var_docs],
    )


@router.get("/ready", response_model=DocumentListResponse)
def fn_get_ready_documents(
    db: Session = Depends(fn_get_db),
    current_user=Depends(fn_get_current_user),
):
    """
    GET /api/v1/documents/ready — alias for listing ready documents.
    Explicit endpoint used by chat document selector dropdowns.
    """
    var_docs = var_doc_service.fn_list_ready_documents(db)
    return DocumentListResponse(
        total=len(var_docs),
        documents=[DocumentResponse.model_validate(d) for d in var_docs],
    )


@router.get("/{doc_id}", response_model=DocumentResponse)
def fn_get_document(
    doc_id: int,
    db: Session = Depends(fn_get_db),
    current_user=Depends(fn_get_current_user),
):
    """
    GET /api/v1/documents/{doc_id} — get a single document's metadata.
    Returns 404 if the document doesn't exist.
    Users can only access documents with status='ready'.
    """
    var_doc = var_doc_service.fn_get_document(db, doc_id)
    # Regular users can only see ready documents
    if current_user.user_role != "admin" and var_doc.status != "ready":
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Document is not available",
        )
    return DocumentResponse.model_validate(var_doc)