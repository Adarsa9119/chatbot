"""
database package — SQLAlchemy session, connection helpers, and all CRUD modules.

Usage:
    from database import fn_get_db, fn_check_db_connection
    from database.crud_users import fn_get_user_by_email, fn_create_user
"""

from database.connection import engine, SessionLocal
from database.session import fn_get_db, fn_check_db_connection

from database.crud_users import (
    fn_get_user_by_id,
    fn_get_user_by_email,
    fn_create_user,
    fn_update_user,
    fn_delete_user,
    fn_list_users,
    fn_count_users,
)
from database.crud_documents import (
    fn_create_document,
    fn_get_document_by_id,
    fn_get_user_documents,
    fn_update_document_status,
    fn_delete_document,
    fn_count_documents,
)
from database.crud_chunks import (
    fn_insert_chunks,
    fn_get_chunks_by_document,
    fn_delete_chunks_by_document,
    fn_search_similar_chunks,
)
from database.crud_chat import (
    fn_create_message,
    fn_get_session_messages,
    fn_get_message_by_id,
    fn_delete_message,
)
from database.crud_sessions import (
    fn_create_session,
    fn_get_session_by_id,
    fn_get_user_sessions,
    fn_rename_session,
    fn_delete_session,
    fn_count_sessions,
)
from database.crud_refresh_tokens import (
    fn_store_refresh_token,
    fn_get_refresh_token,
    fn_revoke_refresh_token,
    fn_revoke_all_user_tokens,
)
from database.crud_audit_logs import (
    fn_create_audit_log,
    fn_get_audit_logs,
    fn_count_audit_logs,
)
from database.crud_password_resets import (
    fn_create_password_reset,
    fn_get_password_reset_by_token_hash,
    fn_mark_password_reset_used,
    fn_delete_expired_resets,
)
from database.crud_email_verifications import (
    fn_create_email_verification,
    fn_get_verification_by_token_hash,
    fn_mark_verification_used,
    fn_delete_expired_verifications,
)

__all__ = [
    # connection
    "engine", "SessionLocal",
    # session
    "fn_get_db", "fn_check_db_connection",
    # users
    "fn_get_user_by_id", "fn_get_user_by_email", "fn_create_user",
    "fn_update_user", "fn_delete_user", "fn_list_users", "fn_count_users",
    # documents
    "fn_create_document", "fn_get_document_by_id", "fn_get_user_documents",
    "fn_update_document_status", "fn_delete_document", "fn_count_documents",
    # chunks
    "fn_insert_chunks", "fn_get_chunks_by_document",
    "fn_delete_chunks_by_document", "fn_search_similar_chunks",
    # chat
    "fn_create_message", "fn_get_session_messages",
    "fn_get_message_by_id", "fn_delete_message",
    # sessions
    "fn_create_session", "fn_get_session_by_id", "fn_get_user_sessions",
    "fn_rename_session", "fn_delete_session", "fn_count_sessions",
    # refresh tokens
    "fn_store_refresh_token", "fn_get_refresh_token",
    "fn_revoke_refresh_token", "fn_revoke_all_user_tokens",
    # audit logs
    "fn_create_audit_log", "fn_get_audit_logs", "fn_count_audit_logs",
    # password resets
    "fn_create_password_reset", "fn_get_password_reset_by_token_hash",
    "fn_mark_password_reset_used", "fn_delete_expired_resets",
    # email verifications
    "fn_create_email_verification", "fn_get_verification_by_token_hash",
    "fn_mark_verification_used", "fn_delete_expired_verifications",
]