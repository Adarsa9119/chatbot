"""
session_router.py — Chat session management endpoints.
Users can create, list, rename, and delete their own chat sessions.

Change Tracker:
v1.0 — initial
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import Optional

from config.database import fn_get_db
from middleware.auth_middleware import fn_get_current_user
from controllers.session_controller import session_controller
from schemas.session_schema import (
    SessionCreateRequest,
    SessionRenameRequest,
    SessionResponse,
    SessionListResponse,
    SessionCreateResponse,
    SessionDeleteResponse,
    SessionRenameResponse,
)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("", response_model=SessionCreateResponse, status_code=201)
def fn_create_session(
    body: SessionCreateRequest = None,
    request: Request = None,
    db: Session = Depends(fn_get_db),
    current_user=Depends(fn_get_current_user),
):
    """
    POST /api/v1/sessions — create a new chat session.

    Sessions are created with the default title 'New Chat'.
    The title is auto-updated after the first message using LLM.
    Optionally pass { "title": "Custom title" } in the request body.
    """
    var_title = body.title if body else None
    return session_controller.fn_handle_create_session(
        db=db,
        request=request,
        current_user=current_user,
        title=var_title,
    )


@router.get("", response_model=SessionListResponse)
def fn_list_sessions(
    db: Session = Depends(fn_get_db),
    current_user=Depends(fn_get_current_user),
):
    """
    GET /api/v1/sessions — list all sessions for the current user.

    Returns sessions ordered by most recently updated (for sidebar history).
    Each session includes: session_id, title, created_at, updated_at.
    """
    return session_controller.fn_handle_list_sessions(
        db=db,
        current_user=current_user,
    )


@router.get("/{session_id}", response_model=dict)
def fn_get_session(
    session_id: int,
    db: Session = Depends(fn_get_db),
    current_user=Depends(fn_get_current_user),
):
    """
    GET /api/v1/sessions/{session_id} — get session summary.

    Returns:
        { session_id, title, message_count, created_at, updated_at }

    Raises 404 if not found, 403 if not owned by current user.
    """
    return session_controller.fn_handle_get_session(
        db=db,
        session_id=session_id,
        current_user=current_user,
    )


@router.patch("/{session_id}", response_model=SessionRenameResponse)
def fn_rename_session(
    session_id: int,
    body: SessionRenameRequest,
    request: Request,
    db: Session = Depends(fn_get_db),
    current_user=Depends(fn_get_current_user),
):
    """
    PATCH /api/v1/sessions/{session_id} — rename a chat session.

    Body: { "title": "New session title" }
    Title cannot be empty.
    Raises 404 if not found, 403 if not owned by current user.
    """
    return session_controller.fn_handle_rename_session(
        db=db,
        request=request,
        session_id=session_id,
        new_title=body.title,
        current_user=current_user,
    )


@router.delete("/{session_id}", response_model=SessionDeleteResponse)
def fn_delete_session(
    session_id: int,
    request: Request,
    db: Session = Depends(fn_get_db),
    current_user=Depends(fn_get_current_user),
):
    """
    DELETE /api/v1/sessions/{session_id} — delete session and all its messages.

    Cascades: deletes all ChatMessages associated with this session.
    Raises 404 if not found, 403 if not owned by current user.
    """
    return session_controller.fn_handle_delete_session(
        db=db,
        request=request,
        session_id=session_id,
        current_user=current_user,
    )