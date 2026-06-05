"""
test_auth.py — Unit and integration tests for authentication endpoints.
Tests: register, login, logout, me, refresh token.

Run with:
    pytest tests/test_auth.py -v

Change Tracker:
v1.0 — initial
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.database import Base
from config.settings import settings
from main import app
from config.database import fn_get_db

# ── In-memory SQLite for tests ─────────────────────────────────────────
SQLALCHEMY_TEST_URL = "sqlite:///./test_temp.db"
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
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def registered_user(client):
    """Register and return a test user."""
    var_payload = {
        "user_name": "testuser",
        "user_email": "testuser@example.com",
        "password": "TestPass123",
        "confirm_password": "TestPass123",
    }
    var_resp = client.post("/api/v1/auth/register", json=var_payload)
    assert var_resp.status_code == 201
    return var_payload


# ── Register ────────────────────────────────────────────────────────────

class TestRegister:
    def test_register_success(self, client):
        var_resp = client.post("/api/v1/auth/register", json={
            "user_name": "newuser",
            "user_email": "newuser@example.com",
            "password": "Pass@1234",
            "confirm_password": "Pass@1234",
        })
        assert var_resp.status_code == 201
        var_data = var_resp.json()
        assert "user" in var_data
        assert var_data["user"]["user_email"] == "newuser@example.com"

    def test_register_duplicate_email(self, client, registered_user):
        var_resp = client.post("/api/v1/auth/register", json={
            "user_name": "anotheruser",
            "user_email": registered_user["user_email"],
            "password": "Pass@1234",
            "confirm_password": "Pass@1234",
        })
        assert var_resp.status_code == 409

    def test_register_password_mismatch(self, client):
        var_resp = client.post("/api/v1/auth/register", json={
            "user_name": "mismatch",
            "user_email": "mismatch@example.com",
            "password": "Pass@1234",
            "confirm_password": "DifferentPass",
        })
        assert var_resp.status_code in (400, 422)

    def test_register_short_password(self, client):
        var_resp = client.post("/api/v1/auth/register", json={
            "user_name": "shortpass",
            "user_email": "short@example.com",
            "password": "abc",
            "confirm_password": "abc",
        })
        assert var_resp.status_code in (400, 422)

    def test_register_invalid_email(self, client):
        var_resp = client.post("/api/v1/auth/register", json={
            "user_name": "bademail",
            "user_email": "not-an-email",
            "password": "Pass@1234",
            "confirm_password": "Pass@1234",
        })
        assert var_resp.status_code == 422


# ── Login ───────────────────────────────────────────────────────────────

class TestLogin:
    def test_login_success(self, client, registered_user):
        var_resp = client.post("/api/v1/auth/login", json={
            "user_email": registered_user["user_email"],
            "password": registered_user["password"],
        })
        assert var_resp.status_code == 200
        var_data = var_resp.json()
        assert "access_token" in var_data or "user" in var_data

    def test_login_wrong_password(self, client, registered_user):
        var_resp = client.post("/api/v1/auth/login", json={
            "user_email": registered_user["user_email"],
            "password": "WrongPassword",
        })
        assert var_resp.status_code == 401

    def test_login_unknown_email(self, client):
        var_resp = client.post("/api/v1/auth/login", json={
            "user_email": "nobody@example.com",
            "password": "SomePass123",
        })
        assert var_resp.status_code == 401

    def test_login_missing_fields(self, client):
        var_resp = client.post("/api/v1/auth/login", json={
            "user_email": "someone@example.com",
        })
        assert var_resp.status_code == 422


# ── Me endpoint ─────────────────────────────────────────────────────────

class TestMe:
    def test_me_unauthenticated(self, client):
        var_resp = client.get("/api/v1/auth/me")
        assert var_resp.status_code == 401

    def test_me_authenticated(self, client, registered_user):
        # Login first
        var_login = client.post("/api/v1/auth/login", json={
            "user_email": registered_user["user_email"],
            "password": registered_user["password"],
        })
        assert var_login.status_code == 200
        # Cookie is set automatically by TestClient
        var_me = client.get("/api/v1/auth/me")
        assert var_me.status_code == 200
        assert var_me.json()["user_email"] == registered_user["user_email"]


# ── Logout ──────────────────────────────────────────────────────────────

class TestLogout:
    def test_logout_clears_session(self, client, registered_user):
        client.post("/api/v1/auth/login", json={
            "user_email": registered_user["user_email"],
            "password": registered_user["password"],
        })
        var_logout = client.post("/api/v1/auth/logout")
        assert var_logout.status_code == 200

        # After logout, /me should return 401
        var_me = client.get("/api/v1/auth/me")
        assert var_me.status_code == 401