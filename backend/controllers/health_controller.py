"""
health_controller.py — Health check controller.
Used by load balancers, Docker, and monitoring tools.

Change Tracker:
v1.0 — initial
"""

from sqlalchemy.orm import Session
from config.database import fn_check_db_connection
from config.settings import settings
from config.logging_config import logger
from services.embedding_service import embedding_service
from schemas.health_schema import HealthResponse, DetailedHealthResponse


class HealthController:
    """
    Health check endpoints:
    - fn_handle_ping         — simple liveness check
    - fn_handle_health       — db + embedding model readiness
    - fn_handle_ready        — strict readiness gate for load balancers
    """

    def fn_handle_ping(self) -> dict:
        """GET /health/ping — ultra-lightweight liveness probe."""
        return {"status": "ok", "message": "pong"}

    def fn_handle_health(self, db: Session) -> HealthResponse:
        """
        GET /health — checks DB connectivity and embedding model status.
        Returns overall status plus individual component checks.
        """
        var_db_ok = fn_check_db_connection()
        var_model_ok = embedding_service._model is not None

        var_status = "healthy" if (var_db_ok and var_model_ok) else "degraded"

        return HealthResponse(
            status=var_status,
            database=var_db_ok,
            embedding_model=var_model_ok,
            app_env=settings.APP_ENV,
        )

    def fn_handle_detailed(self, db: Session) -> DetailedHealthResponse:
        """
        GET /health/detailed — extended health with version info.
        Admin use only — exposes config details.
        """
        var_db_ok = fn_check_db_connection()
        var_model_ok = embedding_service._model is not None

        var_status = "healthy" if (var_db_ok and var_model_ok) else "degraded"

        return DetailedHealthResponse(
            status=var_status,
            database=var_db_ok,
            embedding_model=var_model_ok,
            app_name=settings.APP_NAME,
            app_env=settings.APP_ENV,
            embedding_model_name=settings.EMBEDDING_MODEL,
            llm_model=settings.LLM_MODEL,
        )

    def fn_handle_ready(self, db: Session) -> dict:
        """
        GET /health/ready — strict readiness check.
        Returns 200 only when both DB and model are ready.
        Used by container orchestration to gate traffic.
        """
        var_db_ok = fn_check_db_connection()
        var_model_ok = embedding_service._model is not None

        if not var_db_ok:
            logger.warning("Readiness check failed: DB not reachable")
            return {"ready": False, "reason": "Database not reachable"}

        if not var_model_ok:
            logger.warning("Readiness check failed: embedding model not loaded")
            return {"ready": False, "reason": "Embedding model not loaded"}

        return {"ready": True}


# ── Singleton ──────────────────────────────────────────────────────────
health_controller = HealthController()