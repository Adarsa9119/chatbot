"""
exception_middleware.py — Global exception handler middleware.
Catches unhandled exceptions and returns structured JSON error responses.
Prevents raw Python tracebacks from leaking to clients.

Change Tracker:
v1.0 — initial
"""

import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from config.logging_config import logger
from config.settings import settings


class ExceptionMiddleware(BaseHTTPMiddleware):
    """
    Catches all unhandled exceptions and formats them as JSON.

    In production (APP_DEBUG=False): hides internal error details.
    In development (APP_DEBUG=True): includes traceback in response.
    """

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            var_tb = traceback.format_exc()
            logger.error(
                f"Unhandled exception on {request.method} {request.url.path}: "
                f"{type(e).__name__}: {e}\n{var_tb}"
            )

            var_detail = "An unexpected internal server error occurred."
            if settings.APP_DEBUG:
                var_detail = f"{type(e).__name__}: {str(e)}"

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": var_detail,
                    "error_type": type(e).__name__,
                    "path": str(request.url.path),
                },
            )


def fn_register_exception_handlers(app) -> None:
    """
    Register FastAPI exception handlers for validation errors and HTTP exceptions.
    Call this in main.py after app creation.

    Usage:
        from middleware.exception_middleware import fn_register_exception_handlers
        fn_register_exception_handlers(app)
    """

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Return 422 with structured error list for Pydantic validation failures."""
        var_errors = []
        for var_error in exc.errors():
            var_errors.append({
                "field": " → ".join(str(loc) for loc in var_error["loc"]),
                "message": var_error["msg"],
                "type": var_error["type"],
            })
        logger.warning(
            f"Validation error on {request.method} {request.url.path}: {var_errors}"
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Request validation failed",
                "errors": var_errors,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Return structured JSON for all HTTP exceptions (404, 401, 403, etc.)."""
        logger.info(
            f"HTTP {exc.status_code} on {request.method} {request.url.path}: "
            f"{exc.detail}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Catch-all for any exception not handled above."""
        var_tb = traceback.format_exc()
        logger.error(
            f"Unhandled {type(exc).__name__} on "
            f"{request.method} {request.url.path}: {exc}\n{var_tb}"
        )
        var_detail = "An unexpected error occurred."
        if settings.APP_DEBUG:
            var_detail = f"{type(exc).__name__}: {str(exc)}"

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": var_detail},
        )