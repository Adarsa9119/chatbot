-- 01_create_extension.sql
-- Run first: enables pgvector in your PostgreSQL 16 database.
-- Run as postgres superuser.

CREATE EXTENSION IF NOT EXISTS vector;