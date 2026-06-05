"""
main.py — FastAPI application entrypoint.
FIXED:
  - CORS middleware added (original spec missing — every frontend call would fail)
  - Embedding model loaded ONCE in lifespan (not per request)
  - slowapi rate limiter registered on app
  - All directories created at startup
  - pgvector extension ensured at startup
Change Tracker:
  v1.0 — initial
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from config.settings import settings
from config.logging_config import fn_setup_logging, logger
from config.database import fn_create_all_tables, fn_check_db_connection, engine, SessionLocal

# ── Import all models so Alembic/SQLAlchemy can see them ────
from models import (
    UsersModel, DocumentsModel, ChunksModel,
    ChatSessionsModel, ChatMessagesModel,
    RefreshTokensModel, AuditLogsModel,
)

# ── Routers ──────────────────────────────────────────────────
from routers.auth_router import router as auth_router
from routers.admin_router import router as admin_router
from routers.user_router import router as user_router
from routers.chat_router import router as chat_router
from routers.audit_router import router as audit_router
from routers.health_router import router as health_router

# ── Embedding model singleton ────────────────────────────────
from services.embedding_service import embedding_service


# ── Lifespan: startup + shutdown ─────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan:
    STARTUP:
      1. Init logging
      2. Create upload/static directories
      3. Create DB tables
      4. Enable pgvector extension
      5. Create pgvector IVFFlat index (FIXED: was missing)
      6. Load embedding model ONCE (expensive — ~2s first time)
    SHUTDOWN:
      - Dispose DB engine connections
    """
    # ── 1. Logging ───────────────────────────────────────────
    fn_setup_logging()
    logger.info(f"Starting {settings.APP_NAME} [{settings.APP_ENV}]")

    # ── 2. Directories ───────────────────────────────────────
    for var_dir in [
        settings.UPLOAD_DIR,
        settings.PROCESSED_DIR,
        settings.FAILED_DIR,
        settings.TEMP_DIR,
        settings.STATIC_DIR + "/profile_images",
        settings.STATIC_DIR + "/exports",
        "storage/logs",
    ]:
        Path(var_dir).mkdir(parents=True, exist_ok=True)
    logger.info("Directories ready")

    # ── 3. DB Tables ─────────────────────────────────────────
    if fn_check_db_connection():
        fn_create_all_tables()
        logger.info("Database tables ready")
    else:
        logger.critical("Cannot connect to database — check DB_HOST/PORT/NAME in .env")

    # ── 4. pgvector extension ────────────────────────────────
    try:
        with engine.connect() as var_conn:
            var_conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            var_conn.commit()
        logger.info("pgvector extension enabled")
    except Exception as e:
        logger.warning(f"pgvector extension check: {e}")

    # ── 5. pgvector IVFFlat index ────────────────────────────
    # FIXED: Without this index, similarity search is a full table scan (O(n)).
    # Build after 100+ rows — safe to run multiple times (IF NOT EXISTS).
    try:
        with engine.connect() as var_conn:
            var_conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_chunks_embedding
                ON chunks USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """))
            var_conn.commit()
        logger.info("pgvector IVFFlat index ready")
    except Exception as e:
        logger.warning(f"pgvector index (non-critical at first run): {e}")

    # ── 6. Load embedding model ──────────────────────────────
    try:
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL} …")
        from sentence_transformers import SentenceTransformer
        var_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        embedding_service.fn_set_model(var_model)
        app.state.embedding_model = var_model
        logger.info("Embedding model loaded successfully")
    except Exception as e:
        logger.critical(f"Embedding model failed to load: {e}")
        app.state.embedding_model = None

    logger.info(f"{settings.APP_NAME} started on port {settings.APP_PORT}")

    yield  # ← app is running

    # ── Shutdown ─────────────────────────────────────────────
    logger.info("Shutting down — disposing DB connections")
    engine.dispose()


# ── Rate limiter ─────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

# ── FastAPI app ──────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Secure Document RAG Chatbot API",
    docs_url="/api/docs" if settings.APP_DEBUG else None,
    redoc_url="/api/redoc" if settings.APP_DEBUG else None,
    lifespan=lifespan,
)

# ── Rate limiter state ───────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ─────────────────────────────────────────────────────
# FIXED: Without this, every frontend API call fails with CORS error.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,       # Required for HTTPonly cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files ─────────────────────────────────────────────
app.mount(
    "/static",
    StaticFiles(directory=settings.STATIC_DIR, check_dir=False),
    name="static",
)

# ── API Routers (all under /api/v1) ──────────────────────────
API_PREFIX = "/api/v1"

app.include_router(auth_router,    prefix=API_PREFIX)
app.include_router(admin_router,   prefix=API_PREFIX)
app.include_router(user_router,    prefix=API_PREFIX)
app.include_router(chat_router,    prefix=API_PREFIX)
app.include_router(audit_router,   prefix=API_PREFIX)
app.include_router(health_router,  prefix=API_PREFIX)


# ── Global exception handler ─────────────────────────────────
@app.exception_handler(Exception)
async def fn_global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc} — {request.method} {request.url}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ── Root endpoint ─────────────────────────────────────────────
@app.get("/")
def fn_root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/api/v1/health",
    }


# ── Dev runner ───────────────────────────────────────────────
# Run from backend/ directory:
#   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
        # watchfiles is required on Windows for --reload to work
        # FIXED: added watchfiles to requirements.txt
    )