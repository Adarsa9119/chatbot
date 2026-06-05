"""
gunicorn.conf.py — Production Gunicorn configuration for secure_doc_chatbot.

Usage:
    gunicorn main:app -c deployment/gunicorn.conf.py

Docs: https://docs.gunicorn.org/en/stable/settings.html
"""

import multiprocessing
import os

# ── Binding ───────────────────────────────────────────────────────────────────
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")

# ── Workers ───────────────────────────────────────────────────────────────────
# Recommended formula: (2 × CPU cores) + 1
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

# Use UvicornWorker to run the ASGI FastAPI app
worker_class = "uvicorn.workers.UvicornWorker"

# Number of worker threads per worker process (UvicornWorker uses async I/O,
# so threads are typically left at 1)
threads = int(os.getenv("GUNICORN_THREADS", 1))

# ── Timeouts ──────────────────────────────────────────────────────────────────
# Generous timeout for long RAG completions
timeout = int(os.getenv("GUNICORN_TIMEOUT", 120))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", 30))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", 5))

# ── Request limits ────────────────────────────────────────────────────────────
# 55 MB to accommodate the 50 MB upload limit + headers
limit_request_line   = 8190
limit_request_fields = 200
limit_request_field_size = 0  # unlimited header value size

# ── Logging ───────────────────────────────────────────────────────────────────
accesslog  = os.getenv("GUNICORN_ACCESS_LOG", "-")   # stdout
errorlog   = os.getenv("GUNICORN_ERROR_LOG",  "-")   # stderr
loglevel   = os.getenv("GUNICORN_LOG_LEVEL", "info")
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s '
    '"%(f)s" "%(a)s" %(D)sµs'
)

# ── Process naming ────────────────────────────────────────────────────────────
proc_name = "docchat_backend"

# ── Security ──────────────────────────────────────────────────────────────────
# Forward the X-Forwarded-* headers from Nginx / load balancer
forwarded_allow_ips = os.getenv("GUNICORN_FORWARDED_IPS", "127.0.0.1")

# ── Lifecycle hooks ───────────────────────────────────────────────────────────

def on_starting(server):
    server.log.info("Gunicorn starting — docchat backend")


def post_fork(server, worker):
    server.log.info(f"Worker spawned (pid: {worker.pid})")


def worker_exit(server, worker):
    server.log.info(f"Worker exiting (pid: {worker.pid})")


def on_exit(server):
    server.log.info("Gunicorn shutting down — docchat backend")