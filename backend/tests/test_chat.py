"""
test_chat.py — Tests for the chat endpoints: session creation, asking questions,
message history retrieval.

Run with:
    pytest tests/test_chat.py -v

Change Tracker:
v1.0 — initial
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.database import Base, fn_get_db
from main import app

# ── Test DB ─────────────────────────────────────────────────────────────
SQLALCHEMY_TEST_URL = "sqlite:///./test_chat_temp.db"
engine_test = create_engine(
    SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[fn_get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_client(client):
    """Authenticated regular user client."""
    client.post("/api/v1/auth/register", json={
        "user_name": "chatuser",
        "user_email": "chatuser@test.com",
        "password": "Chat@1234",
        "confirm_password": "Chat@1234",
    })
    db = TestingSessionLocal()
    from database.crud_users import fn_get_user_by_email, fn_update_user
    var_user = fn_get_user_by_email(db, "chatuser@test.com")
    if var_user:
        fn_update_user(db, var_user.user_id, is_verified=True)
    db.close()

    client.post("/api/v1/auth/login", json={
        "user_email": "chatuser@test.com",
        "password": "Chat@1234",
    })
    return client


# ── Session management ──────────────────────────────────────────────────

class TestSessions:
    def test_create_session_unauthenticated(self, client):
        var_resp = client.post("/api/v1/sessions")
        assert var_resp.status_code == 401

    def test_create_session_authenticated(self, auth_client):
        var_resp = auth_client.post("/api/v1/sessions")
        assert var_resp.status_code == 201
        var_data = var_resp.json()
        assert "session_id" in var_data

    def test_list_sessions(self, auth_client):
        auth_client.post("/api/v1/sessions")
        auth_client.post("/api/v1/sessions")
        var_resp = auth_client.get("/api/v1/sessions")
        assert var_resp.status_code == 200
        var_data = var_resp.json()
        assert var_data["total"] >= 2

    def test_delete_session(self, auth_client):
        var_create = auth_client.post("/api/v1/sessions")
        var_session_id = var_create.json()["session_id"]
        var_resp = auth_client.delete(f"/api/v1/sessions/{var_session_id}")
        assert var_resp.status_code == 200

    def test_delete_nonexistent_session(self, auth_client):
        var_resp = auth_client.delete("/api/v1/sessions/99999")
        assert var_resp.status_code == 404

    def test_rename_session(self, auth_client):
        var_create = auth_client.post("/api/v1/sessions")
        var_session_id = var_create.json()["session_id"]
        var_resp = auth_client.patch(
            f"/api/v1/sessions/{var_session_id}",
            json={"title": "My renamed session"},
        )
        assert var_resp.status_code == 200
        assert var_resp.json()["title"] == "My renamed session"


# ── Chat ask ────────────────────────────────────────────────────────────

class TestChatAsk:
    def test_ask_unauthenticated(self, client):
        var_resp = client.post("/api/v1/chat/ask", json={
            "session_id": 1,
            "question": "What is this about?",
        })
        assert var_resp.status_code == 401

    def test_ask_nonexistent_session(self, auth_client):
        var_resp = auth_client.post("/api/v1/chat/ask", json={
            "session_id": 99999,
            "question": "Test question",
        })
        assert var_resp.status_code == 404

    @patch("services.vector_service.vector_service.fn_search")
    @patch("services.llm_service.llm_service.fn_answer_from_context")
    def test_ask_success(self, mock_llm, mock_search, auth_client):
        """Mock vector search and LLM to test chat flow without actual model calls."""
        mock_search.return_value = [
            {
                "chunk_id": 1,
                "doc_id": 1,
                "doc_title": "Test Document",
                "chunk_text": "This is a test chunk.",
                "chunk_index": 0,
                "similarity": 0.95,
                "metadata": None,
            }
        ]
        mock_llm.return_value = "Based on the document, this is a test answer."

        var_session = auth_client.post("/api/v1/sessions").json()
        var_resp = auth_client.post("/api/v1/chat/ask", json={
            "session_id": var_session["session_id"],
            "question": "What is this about?",
        })
        assert var_resp.status_code == 200
        var_data = var_resp.json()
        assert "answer" in var_data
        assert "sources" in var_data

    def test_ask_empty_question(self, auth_client):
        var_session = auth_client.post("/api/v1/sessions").json()
        var_resp = auth_client.post("/api/v1/chat/ask", json={
            "session_id": var_session["session_id"],
            "question": "",
        })
        assert var_resp.status_code in (400, 422)


# ── Chat history ────────────────────────────────────────────────────────

class TestChatHistory:
    def test_history_unauthenticated(self, client):
        var_resp = client.get("/api/v1/chat/history/1")
        assert var_resp.status_code == 401

    def test_history_empty_session(self, auth_client):
        var_session = auth_client.post("/api/v1/sessions").json()
        var_resp = auth_client.get(f"/api/v1/chat/history/{var_session['session_id']}")
        assert var_resp.status_code == 200
        var_data = var_resp.json()
        assert var_data["messages"] == []