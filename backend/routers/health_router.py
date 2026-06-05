"""
health_router.py — Health check endpoint.
Change Tracker:
  v1.0 — initial
"""

from fastapi import APIRouter, Request
from config.database import fn_check_db_connection
from schemas.health_schema import HealthResponse


router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
def fn_health_check(request: Request):
    """GET /api/v1/health — service health status."""
    var_db_ok = fn_check_db_connection()
    var_model_ok = hasattr(request.app.state, "embedding_model") and request.app.state.embedding_model is not None

    return HealthResponse(
        status="ok" if var_db_ok else "degraded",
        database="connected" if var_db_ok else "disconnected",
        embedding_model="loaded" if var_model_ok else "not loaded",
    )