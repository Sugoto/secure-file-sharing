import pytest
from fastapi.testclient import TestClient
import os
import tempfile
from unittest.mock import patch
from app.main import app
from app.services.database import init_db, DATABASE_PATH

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    """Create a fresh test database for each test"""
    global DATABASE_PATH
    temp_db = tempfile.NamedTemporaryFile(delete=False)
    original_path = DATABASE_PATH
    DATABASE_PATH = temp_db.name

    init_db()

    yield DATABASE_PATH

    temp_db.close()
    try:
        os.unlink(temp_db.name)
    except:
        pass
    DATABASE_PATH = original_path


@pytest.fixture(autouse=True)
def cleanup_uploaded_files():
    """Clean up any uploaded test files after each test"""
    yield
    if os.path.exists("uploads"):
        for filename in os.listdir("uploads"):
            if filename.startswith("test") or filename.startswith((".", "_")):
                try:
                    os.remove(os.path.join("uploads", filename))
                except:
                    pass


@pytest.fixture
def test_user_token():
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "role": "user",
        "mfa_enabled": False,
    }
    client.post("/auth/register", json=user_data)
    response = client.post(
        "/auth/login", json={"username": "testuser", "password": "testpass123"}
    )
    return response.json()["access_token"]


@pytest.fixture
def admin_token():
    user_data = {
        "username": "admin",
        "email": "admin@example.com",
        "password": "adminpass123",
        "role": "admin",
        "mfa_enabled": False,
    }
    client.post("/auth/register", json=user_data)
    response = client.post(
        "/auth/login", json={"username": "admin", "password": "adminpass123"}
    )
    return response.json()["access_token"]


def test_register_user():
    response = client.post(
        "/auth/register",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "password123",
            "role": "user",
            "mfa_enabled": False,
        },
    )

    if response.status_code == 200:
        assert "message" in response.json()
        assert response.json()["message"] == "User registered successfully"
    else:
        assert response.status_code == 400
        assert "detail" in response.json()
        assert "already registered" in response.json()["detail"]


def test_login_user():
    client.post(
        "/auth/register",
        json={
            "username": "logintest",
            "email": "login@example.com",
            "password": "password123",
            "role": "user",
            "mfa_enabled": False,
        },
    )

    response = client.post(
        "/auth/login", json={"username": "logintest", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_upload_file(test_user_token):
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(b"test content")
        tmp_file.flush()

        files = {
            "file": ("test.txt", open(tmp_file.name, "rb"), "text/plain"),
            "iv": ("iv", b"mock_iv", "application/octet-stream"),
            "salt": ("salt", b"mock_salt", "application/octet-stream"),
        }
        headers = {"Authorization": f"Bearer {test_user_token}"}

        response = client.post("/files/upload", files=files, headers=headers)
        assert response.status_code == 200
        assert "message" in response.json()

    os.unlink(tmp_file.name)


def test_list_files(test_user_token):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    response = client.get("/files/list", headers=headers)
    assert response.status_code == 200
    assert "owned_files" in response.json()
    assert "shared_files" in response.json()


@patch("app.services.security.SecurityService.send_mfa_code")
def test_mfa_flow(mock_send_mfa):
    client.post(
        "/auth/register",
        json={
            "username": "mfauser",
            "email": "mfa@example.com",
            "password": "password123",
            "role": "user",
            "mfa_enabled": True,
        },
    )

    response = client.post(
        "/auth/login", json={"username": "mfauser", "password": "password123"}
    )
    assert response.status_code == 200
    assert response.json()["require_mfa"] == True

    mock_send_mfa.assert_called_once()
    response = client.post(
        "/auth/verify-mfa",
        json={
            "username": "mfauser",
            "code": "123456",
        },
    )
    assert response.status_code == 401


def test_file_sharing(test_user_token, admin_token):
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(b"test content")
        tmp_file.flush()

        files = {
            "file": ("test.txt", open(tmp_file.name, "rb"), "text/plain"),
            "iv": ("iv", b"mock_iv", "application/octet-stream"),
            "salt": ("salt", b"mock_salt", "application/octet-stream"),
        }
        headers = {"Authorization": f"Bearer {test_user_token}"}

        upload_response = client.post("/files/upload", files=files, headers=headers)

        list_response = client.get("/files/list", headers=headers)
        file_id = list_response.json()["owned_files"][0]["id"]

        share_response = client.post(
            "/files/share",
            headers=headers,
            json={
                "file_id": file_id,
                "shared_with_username": "admin",
                "permissions": "view",
                "expires_in_hours": 24,
            },
        )
        assert share_response.status_code == 200

    os.unlink(tmp_file.name)


def test_admin_functions(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get("/auth/users", headers=headers)
    assert response.status_code == 200
    assert "users" in response.json()

    response = client.put(
        "/auth/users/1/role", headers=headers, params={"new_role": "user"}
    )
    assert response.status_code == 200


def test_invalid_token():
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/files/list", headers=headers)
    assert response.status_code == 403


def test_cleanup():
    for filename in os.listdir("uploads"):
        if filename.startswith("test"):
            os.remove(os.path.join("uploads", filename))
