"""
Phase 2 Automated Verification Suite
Tests database connections, bcrypt password hashing, JWT issuing and validation,
and authentication API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.database.init_db import init_database
from app.models.db_models import User, Role
from app.security.token_util import hash_password, verify_password, create_access_token, decode_access_token

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Initializes and seeds database before running any tests."""
    init_database()

client = TestClient(app)

def test_password_hashing_and_verification():
    password = "Secur3Password!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token_generation_and_decoding():
    payload = {"sub": "user-12345", "username": "dr_alice", "role": "USER"}
    token = create_access_token(payload)
    assert isinstance(token, str)
    
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user-12345"
    assert decoded["username"] == "dr_alice"
    assert decoded["role"] == "USER"

def test_system_status_endpoint():
    response = client.get("/api/v1/system/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPERATIONAL"
    assert "security_features" in data
    assert data["security_features"]["symmetric_cipher"] == "AES-256-GCM"

def test_user_login_success():
    # Login with seeded user dr_alice_radiology
    response = client.post("/api/v1/auth/login", json={
        "username": "dr_alice_radiology",
        "password": "Password123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["username"] == "dr_alice_radiology"
    assert data["role"] == "USER"

def test_user_login_invalid_password():
    response = client.post("/api/v1/auth/login", json={
        "username": "dr_alice_radiology",
        "password": "WrongPassword!"
    })
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_user_registration_and_duplicate_check():
    import uuid
    random_user = f"clinician_{uuid.uuid4().hex[:6]}"
    response = client.post("/api/v1/auth/register", json={
        "username": random_user,
        "email": f"{random_user}@hospital.org",
        "password": "Password123!",
        "role_name": "USER"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == random_user
    assert "access_token" in data

    # Attempt duplicate registration with same username
    dup_res = client.post("/api/v1/auth/register", json={
        "username": random_user,
        "email": f"different_{random_user}@hospital.org",
        "password": "Password123!",
        "role_name": "USER"
    })
    assert dup_res.status_code == 400
    assert "already taken" in dup_res.json()["detail"]
