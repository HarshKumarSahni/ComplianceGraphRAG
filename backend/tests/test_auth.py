import pytest
from fastapi.testclient import TestClient
from app.main import create_application

app = create_application()
client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    from app.db.database import engine, Base
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def test_signup_success():
    payload = {
        "full_name": "Sarah Connor",
        "email": "sarah.connor@compliance.ai",
        "password": "SecurePassword123!"
    }
    resp = client.post("/api/v1/auth/signup", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["user"]["email"] == "sarah.connor@compliance.ai"
    assert data["data"]["user"]["full_name"] == "Sarah Connor"

def test_signup_duplicate_email_fails():
    payload = {
        "full_name": "Sarah Connor",
        "email": "sarah.connor@compliance.ai",
        "password": "SecurePassword123!"
    }
    client.post("/api/v1/auth/signup", json=payload)
    resp2 = client.post("/api/v1/auth/signup", json=payload)
    assert resp2.status_code == 400
    assert "already exists" in resp2.json()["message"].lower()

def test_login_success():
    signup_payload = {
        "full_name": "Alex Rivera",
        "email": "alex.rivera@compliance.ai",
        "password": "MySecretPassword123"
    }
    client.post("/api/v1/auth/signup", json=signup_payload)

    login_payload = {
        "email": "alex.rivera@compliance.ai",
        "password": "MySecretPassword123"
    }
    resp = client.post("/api/v1/auth/login", json=login_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "access_token" in data["data"]

def test_login_invalid_password_fails():
    signup_payload = {
        "full_name": "Alex Rivera",
        "email": "alex.rivera@compliance.ai",
        "password": "MySecretPassword123"
    }
    client.post("/api/v1/auth/signup", json=signup_payload)

    login_payload = {
        "email": "alex.rivera@compliance.ai",
        "password": "WrongPassword"
    }
    resp = client.post("/api/v1/auth/login", json=login_payload)
    assert resp.status_code == 401

def test_get_me_authenticated():
    signup_payload = {
        "full_name": "Elena Vance",
        "email": "elena.vance@compliance.ai",
        "password": "Password987!"
    }
    signup_resp = client.post("/api/v1/auth/signup", json=signup_payload)
    token = signup_resp.json()["data"]["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    data = me_resp.json()["data"]
    assert data["email"] == "elena.vance@compliance.ai"
    assert data["full_name"] == "Elena Vance"
