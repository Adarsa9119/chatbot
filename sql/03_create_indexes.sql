-- 03_create_indexes.sql
-- FIXED: IVFFlat index on embeddings is CRITICAL for performance.
-- Without it, pgvector does a full table scan on every chat message.
-- Run AFTER inserting at least 100 chunks (index needs data to build).

-- ── B-tree indexes ───────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_users_email        ON users(user_email);
CREATE INDEX IF NOT EXISTS idx_documents_status   ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by ON documents(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_chunks_doc_id      ON chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id   ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id  ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action   ON audit_logs(action);

-- ── pgvector IVFFlat cosine similarity index ─────────────────
-- FIXED: Was missing from original spec.
-- lists=100 works for up to ~1M chunks; increase for larger datasets.
-- ivfflat.probes=10 set per-session in crud_chunks.py for best recall.
CREATE INDEX IF NOT EXISTS idx_chunks_embedding
    ON chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);