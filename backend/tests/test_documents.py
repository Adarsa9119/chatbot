"""
test_documents.py — Tests for document upload, listing, deletion, and status.

Run with:
    pytest tests/test_documents.py -v

Change Tracker:
v1.0 — initial
"""

import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.database import Base, fn_get_db
from main import app

# ── Test DB setup ──────────────────────────────────────────────────────
SQLALCHEMY_TEST_URL = "sqlite:///./test_documents_temp.db"
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
def admin_client(client):
    """Client authenticated as admin."""
    client.post("/api/v1/auth/register", json={
        "user_name": "admin",
        "user_email": "admin@test.com",
        "password": "Admin@1234",
        "confirm_password": "Admin@1234",
    })
    # Manually elevate role in DB
    db = TestingSessionLocal()
    from database.crud_users import fn_get_user_by_email, fn_update_user
    var_user = fn_get_user_by_email(db, "admin@test.com")
    if var_user:
        fn_update_user(db, var_user.user_id, user_role="admin", is_verified=True)
    db.close()

    client.post("/api/v1/auth/login", json={
        "user_email": "admin@test.com",
        "password": "Admin@1234",
    })
    return client


@pytest.fixture
def user_client(client):
    """Client authenticated as regular user."""
    client.post("/api/v1/auth/register", json={
        "user_name": "testuser",
        "user_email": "user@test.com",
        "password": "User@1234",
        "confirm_password": "User@1234",
    })
    db = TestingSessionLocal()
    from database.crud_users import fn_get_user_by_email, fn_update_user
    var_user = fn_get_user_by_email(db, "user@test.com")
    if var_user:
        fn_update_user(db, var_user.user_id, is_verified=True)
    db.close()

    client.post("/api/v1/auth/login", json={
        "user_email": "user@test.com",
        "password": "User@1234",
    })
    return client


def _make_fake_pdf() -> bytes:
    """Create a minimal valid-looking PDF bytes for upload testing."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f \n"
        b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n0\n%%EOF"
    )


# ── Document listing (unauthenticated) ─────────────────────────────────

class TestDocumentListing:
    def test_list_documents_requires_auth(self, client):
        var_resp = client.get("/api/v1/documents")
        assert var_resp.status_code == 401

    def test_list_documents_authenticated(self, user_client):
        var_resp = user_client.get("/api/v1/documents")
        assert var_resp.status_code == 200
        var_data = var_resp.json()
        assert "documents" in var_data
        assert "total" in var_data

    def test_ready_documents_endpoint(self, user_client):
        var_resp = user_client.get("/api/v1/documents/ready")
        assert var_resp.status_code == 200


# ── Admin document upload ───────────────────────────────────────────────

class TestDocumentUpload:
    def test_upload_requires_admin(self, user_client):
        var_pdf = _make_fake_pdf()
        var_resp = user_client.post(
            "/api/v1/admin/documents",
            data={"title": "Test Doc"},
            files={"file": ("test.pdf", io.BytesIO(var_pdf), "application/pdf")},
        )
        assert var_resp.status_code == 403

    def test_upload_missing_title(self, admin_client):
        var_pdf = _make_fake_pdf()
        var_resp = admin_client.post(
            "/api/v1/admin/documents",
            files={"file": ("test.pdf", io.BytesIO(var_pdf), "application/pdf")},
        )
        assert var_resp.status_code == 422

    def test_upload_non_pdf_rejected(self, admin_client):
        var_resp = admin_client.post(
            "/api/v1/admin/documents",
            data={"title": "Not a PDF"},
            files={"file": ("test.txt", io.BytesIO(b"Hello world"), "text/plain")},
        )
        assert var_resp.status_code == 400

    def test_upload_success(self, admin_client):
        var_pdf = _make_fake_pdf()
        var_resp = admin_client.post(
            "/api/v1/admin/documents",
            data={"title": "Test Document", "description": "Test"},
            files={"file": ("test.pdf", io.BytesIO(var_pdf), "application/pdf")},
        )
        assert var_resp.status_code == 201
        var_data = var_resp.json()
        assert "doc_id" in var_data
        assert var_data["title"] == "Test Document"


# ── Admin document delete ───────────────────────────────────────────────

class TestDocumentDelete:
    def test_delete_nonexistent(self, admin_client):
        var_resp = admin_client.delete("/api/v1/admin/documents/99999")
        assert var_resp.status_code == 404

    def test_delete_requires_admin(self, user_client):
        var_resp = user_client.delete("/api/v1/admin/documents/1")
        assert var_resp.status_code == 403