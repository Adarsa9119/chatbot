-- 02_create_tables.sql
-- Run after 01_create_extension.sql
-- Creates all tables in dependency order.

-- ── users ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id         SERIAL PRIMARY KEY,
    user_name       VARCHAR(100) NOT NULL,
    user_email      VARCHAR(255) UNIQUE NOT NULL,
    user_password   TEXT NOT NULL,
    user_role       VARCHAR(20) NOT NULL DEFAULT 'user',
    profile_image_url TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── documents ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS documents (
    doc_id          SERIAL PRIMARY KEY,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    file_path       TEXT NOT NULL,
    file_size_kb    INTEGER,
    ocr_required    BOOLEAN DEFAULT FALSE,
    status          VARCHAR(20) DEFAULT 'processing',  -- processing | ready | failed
    error_message   TEXT,
    uploaded_by     INTEGER REFERENCES users(user_id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── chunks (pgvector) ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id        SERIAL PRIMARY KEY,
    doc_id          INTEGER REFERENCES documents(doc_id) ON DELETE CASCADE,
    chunk_text      TEXT NOT NULL,
    chunk_index     INTEGER,
    embedding       vector(384),        -- all-MiniLM-L6-v2 = 384 dims
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── chat_sessions ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id      SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    title           VARCHAR(255) DEFAULT 'New Chat',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── chat_messages ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS chat_messages (
    message_id      SERIAL PRIMARY KEY,
    session_id      INTEGER REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL,   -- 'user' | 'assistant'
    content         TEXT NOT NULL,
    source_chunk_ids INTEGER[],
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── refresh_tokens ────────────────────────────────────────────
-- FIXED: this table was missing from original spec; logout/revocation requires it.
CREATE TABLE IF NOT EXISTS refresh_tokens (
    token_id        SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    token_hash      TEXT UNIQUE NOT NULL,
    expires_at      TIMESTAMPTZ NOT NULL,
    revoked         BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── audit_logs ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id          SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    action          VARCHAR(100) NOT NULL,
    resource_type   VARCHAR(50),
    resource_id     INTEGER,
    details         JSONB DEFAULT '{}',
    ip_address      VARCHAR(45),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);