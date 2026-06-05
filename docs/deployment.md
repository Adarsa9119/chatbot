# Deployment Guide

---

## Prerequisites

| Tool         | Version  |
|--------------|----------|
| Docker       | 24+      |
| Docker Compose | 2.20+  |
| PostgreSQL   | 15+ (with pgvector extension) |

---

## Local Development

```bash
# 1. Clone the repo
git clone https://github.com/your-org/secure_doc_chatbot.git
cd secure_doc_chatbot

# 2. Copy environment files
cp backend/.env.example backend/.env        # Fill in your secrets
cp deployment/.env.production .env.prod     # For production reference

# 3. Start all services
docker compose up --build

# The app is now available at:
#   Frontend  → http://localhost:3000
#   Backend   → http://localhost:8000
#   Docs      → http://localhost:8000/docs
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable                        | Required | Description                              |
|---------------------------------|----------|------------------------------------------|
| `DATABASE_URL`                  | ✅       | PostgreSQL DSN with pgvector             |
| `SECRET_KEY`                    | ✅       | 64+ char random string for JWT signing  |
| `OPENAI_API_KEY`                | ✅       | OpenAI API key for embeddings + chat    |
| `ACCESS_TOKEN_EXPIRE_MINUTES`   | —        | Default `30`                             |
| `REFRESH_TOKEN_EXPIRE_DAYS`     | —        | Default `7`                              |
| `FRONTEND_URL`                  | —        | For email links, default `http://localhost:5173` |
| `SMTP_HOST`                     | —        | SMTP server host                         |
| `SMTP_PORT`                     | —        | Default `587`                            |
| `SMTP_USER`                     | —        | SMTP username                            |
| `SMTP_PASSWORD`                 | —        | SMTP password                            |
| `APP_DEBUG`                     | —        | `false` in production                    |
| `LOG_LEVEL`                     | —        | `INFO` (production), `DEBUG` (dev)      |

Generate a secure key:
```bash
python -c "import secrets; print(secrets.token_hex(64))"
```

---

## Docker Compose Services

| Service    | Image           | Port  | Description          |
|------------|-----------------|-------|----------------------|
| `db`       | postgres:15     | 5432  | PostgreSQL + pgvector|
| `backend`  | (local build)   | 8000  | FastAPI app          |
| `frontend` | (local build)   | 80    | React + Nginx        |

---

## Database Setup

On first run, Alembic migrations are applied automatically.

Manual migration commands:
```bash
# Create a new migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Apply all pending migrations
docker compose exec backend alembic upgrade head

# Rollback one step
docker compose exec backend alembic downgrade -1
```

Create the initial admin user:
```bash
docker compose exec backend python scripts/create_admin.py \
  --name "Admin" \
  --email "admin@example.com" \
  --password "SecureAdmin1!"
```

---

## Production Deployment

1. Set `APP_DEBUG=false` and `LOG_LEVEL=INFO` in `backend/.env`
2. Set strong `SECRET_KEY` (64+ chars)
3. Configure a real SMTP server
4. Use a managed PostgreSQL instance (e.g. AWS RDS, Supabase) with pgvector enabled
5. Mount an S3-compatible volume or persistent disk for `uploads/`
6. Use the Gunicorn config for production:
   ```bash
   gunicorn main:app -c deployment/gunicorn.conf.py
   ```
7. Put Nginx (or a load balancer) in front of Gunicorn

### SSL / TLS
Configure TLS termination at the Nginx level or use a reverse proxy (Caddy, Traefik).

Example Caddy Caddyfile:
```
docchat.example.com {
  reverse_proxy localhost:8000
  tls admin@example.com
}
```

---

## Health Checks

| Endpoint              | Description                    |
|-----------------------|--------------------------------|
| `GET /api/v1/health`  | Application + DB health check  |

---

## Logs

- Application logs: `storage/logs/app.log` (rotated every 10 MB, 7-day retention)
- Nginx access logs: Docker stdout / `/var/log/nginx/access.log`

View live logs:
```bash
docker compose logs -f backend
docker compose logs -f frontend
```