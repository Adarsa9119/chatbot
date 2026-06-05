"""
user_router.py — User-facing endpoints.
Change Tracker:
  v1.0 — initial
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config.database import fn_get_db
from middleware.auth_middleware import fn_require_user
from services.document_service import DocumentService
from schemas.document_schema import DocumentResponse


router = APIRouter(prefix="/user", tags=["User"])
var_doc_service = DocumentService()


@router.get("/documents", response_model=list[DocumentResponse])
def fn_get_user_documents(
    db: Session = Depends(fn_get_db),
    current_user=Depends(fn_require_user),
):
    """
    GET /api/v1/user/documents — list all 'ready' documents available to chat with.
    Users cannot see processing or failed documents.
    """
    var_docs = var_doc_service.fn_list_ready_documents(db)
    return [DocumentResponse.model_validate(d) for d in var_docs]