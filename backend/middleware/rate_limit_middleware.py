"""
rate_limit_middleware.py — In-memory per-IP rate limiter using slowapi.
Configurable limits per route group (auth, chat, general).

Change Tracker:
v1.0 — initial
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

from config.settings import settings
from config.logging_config import logger


# ── Limiter instance ────────────────────────────────────────────────────
# key_func=get_remote_address → rate limits per client IP.
# Override key_func to use user_id for authenticated limits.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],  # Global fallback
)


def fn_get_limiter() -> Limiter:
    """Return the configured limiter instance."""
    return limiter


def fn_register_rate_limiter(app) -> None:
    """
    Attach the limiter and its error handler to a FastAPI app.

    Usage in main.py:
        from middleware.rate_limit_middleware import fn_register_rate_limiter
        fn_register_rate_limiter(app)

    Then decorate routes:
        @router.post("/login")
        @limiter.limit(settings.RATE_LIMIT_AUTH)
        async def login(request: Request, ...):
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _fn_rate_limit_handler)
    logger.info(
        f"Rate limiter registered — auth={settings.RATE_LIMIT_AUTH} "
        f"chat={settings.RATE_LIMIT_CHAT}"
    )


async def _fn_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom 429 response for rate limit violations.
    Logs the violation with IP address.
    """
    var_ip = get_remote_address(request)
    logger.warning(
        f"Rate limit exceeded: IP={var_ip} path={request.url.path} "
        f"limit={exc.detail}"
    )
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests. Please slow down and try again.",
            "retry_after": "60 seconds",
        },
        headers={"Retry-After": "60"},
    )


# ── Per-route limit decorators (import and use in routers) ───────────────
# Usage:
#   from middleware.rate_limit_middleware import limiter, AUTH_LIMIT, CHAT_LIMIT
#
#   @router.post("/login")
#   @limiter.limit(AUTH_LIMIT)
#   async def login(request: Request, ...):
#       ...

AUTH_LIMIT = settings.RATE_LIMIT_AUTH    # e.g. "10/minute"
CHAT_LIMIT = settings.RATE_LIMIT_CHAT    # e.g. "20/minute"
UPLOAD_LIMIT = "5/minute"                # For file uploads
GENERAL_LIMIT = "60/minute"             # For general API endpoints