"""
End-to-End API Test Suite for CaneCare AI.

Tests all key flows:
1. Signup success
2. Duplicate email rejection
3. Login success (JWT token returned)
4. Login failure with wrong password
5. Accessing /me with valid token vs without token
6. Uploading a valid leaf image for prediction (generated with Pillow in-memory)
7. Uploading an invalid/corrupted non-image file
8. Scan history listing with pagination and filters
"""

import io
import sys
import os

# Add parent directory to sys.path so app module is always found
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

# Create an in-memory SQLite database specifically for test isolation
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the real database session with our test session
app.dependency_overrides[get_db] = override_get_db

# Build fresh test tables
Base.metadata.create_all(bind=test_engine)

client = TestClient(app)


def create_dummy_image(format: str = "JPEG") -> bytes:
    """Generate a valid test image in-memory using Pillow."""
    img = Image.new("RGB", (100, 100), color=(34, 139, 34))  # Forest green color
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Authentication Tests
# ---------------------------------------------------------------------------
def test_signup_success():
    """Verify that a farmer can sign up with valid details and password."""
    payload = {
        "full_name": "Ramesh Patil",
        "email": "ramesh@example.com",
        "password": "Password123",
        "phone": "+91 9876543210",
        "language": "mr"
    }
    response = client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "ramesh@example.com"
    assert data["full_name"] == "Ramesh Patil"
    # Ensure ID is a UUID string (36 characters with hyphens), not an integer like 1 or 2
    assert isinstance(data["id"], str)
    assert len(data["id"]) == 36
    assert "-" in data["id"]
    assert "password" not in data
    assert "hashed_password" not in data


def test_signup_duplicate_email():
    """Verify that signing up with an already registered email is rejected."""
    payload = {
        "full_name": "Duplicate User",
        "email": "ramesh@example.com",
        "password": "Password123",
    }
    response = client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


def test_login_success():
    """Verify valid credentials return a JWT bearer token."""
    payload = {
        "email": "ramesh@example.com",
        "password": "Password123"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "ramesh@example.com"


def test_login_wrong_password():
    """Verify invalid password returns HTTP 401 Unauthorized."""
    payload = {
        "email": "ramesh@example.com",
        "password": "WrongPassword999"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "invalid email or password" in response.json()["detail"].lower()


def test_me_endpoint_with_and_without_token():
    """Verify that /me endpoint rejects unauthenticated access and accepts valid token."""
    # 1. Without token: should return 401 or 403
    unauth_response = client.get("/api/v1/auth/me")
    assert unauth_response.status_code in [401, 403]

    # 2. Login to retrieve token
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "ramesh@example.com",
        "password": "Password123"
    })
    token = login_resp.json()["access_token"]

    # 3. With token: should return user profile
    headers = {"Authorization": f"Bearer {token}"}
    auth_response = client.get("/api/v1/auth/me", headers=headers)
    assert auth_response.status_code == 200
    assert auth_response.json()["email"] == "ramesh@example.com"


# ---------------------------------------------------------------------------
# Prediction Tests
# ---------------------------------------------------------------------------
def test_predict_with_valid_image():
    """Verify uploading a valid sugarcane leaf photo returns diagnosis and advice."""
    # Obtain auth token
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "ramesh@example.com",
        "password": "Password123"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create dummy in-memory image
    image_bytes = create_dummy_image("JPEG")
    files = {"file": ("leaf_test.jpg", image_bytes, "image/jpeg")}
    data = {"language": "mr"}

    response = client.post("/api/v1/predict", headers=headers, files=files, data=data)
    assert response.status_code == 201
    result = response.json()

    assert "scan_id" in result
    assert isinstance(result["scan_id"], str)
    assert len(result["scan_id"]) == 36
    assert result["status"] in ["success", "low_confidence"]
    assert "model_version" in result
    assert result["disclaimer"] is True

    if result["status"] == "success":
        assert result["prediction"] is not None
        assert "confidence" in result["prediction"]
        assert len(result["prediction"]["top3"]) == 3
        assert result["guidance"] is not None
        assert len(result["guidance"]["treatment"]) > 0
        # Verify recommended medicines and nearest agro shops are returned
        assert result["medicines"] is not None
        assert len(result["medicines"]) > 0
        assert "name" in result["medicines"][0]
        assert "dosage" in result["medicines"][0]
        assert result["nearest_medical_shops"] is not None
        assert len(result["nearest_medical_shops"]) > 0
        assert "name" in result["nearest_medical_shops"][0]
        assert "contact_phone" in result["nearest_medical_shops"][0]


def test_predict_with_non_image_file():
    """Verify uploading a text file as an image is rejected."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "ramesh@example.com",
        "password": "Password123"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload plain text disguised as jpg
    fake_file = io.BytesIO(b"This is not a real image data stream")
    files = {"file": ("fake_leaf.jpg", fake_file, "image/jpeg")}

    response = client.post("/api/v1/predict", headers=headers, files=files)
    assert response.status_code == 400
    assert "not a valid" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# History and Disease Library Tests
# ---------------------------------------------------------------------------
def test_history_listing():
    """Verify the logged in user can fetch their paginated scan history."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "ramesh@example.com",
        "password": "Password123"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/history?page=1&limit=10", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)
    assert data["page"] == 1


def test_disease_library_public_endpoints():
    """Verify the disease library is accessible without authentication."""
    # List all diseases in English
    resp_en = client.get("/api/v1/diseases?lang=en")
    assert resp_en.status_code == 200
    diseases = resp_en.json()
    assert len(diseases) >= 5

    # Fetch specific disease details in Marathi
    resp_detail = client.get("/api/v1/diseases/red_rot?lang=mr")
    assert resp_detail.status_code == 200
    detail = resp_detail.json()
    assert detail["code"] == "red_rot"
    assert "तांबोरा" in detail["name"] or "लाल" in detail["name"]
    assert len(detail["symptoms"]) > 0


def test_user_profile_update():
    """Verify updating profile fields (PATCH /api/v1/users/me)."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "ramesh@example.com",
        "password": "Password123"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    update_payload = {
        "full_name": "Ramesh S. Patil",
        "phone": "+91 9999988888",
        "language": "hi"
    }
    resp = client.patch("/api/v1/users/me", json=update_payload, headers=headers)
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["full_name"] == "Ramesh S. Patil"
    assert updated["phone"] == "+91 9999988888"
    assert updated["language"] == "hi"


def test_scan_lifecycle_and_feedback():
    """Verify scan creation, detail retrieval, feedback submission, and scan deletion."""
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "ramesh@example.com",
        "password": "Password123"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Upload scan
    image_bytes = create_dummy_image("PNG")
    files = {"file": ("test_leaf.png", image_bytes, "image/png")}
    pred_resp = client.post("/api/v1/predict", headers=headers, files=files)
    assert pred_resp.status_code == 201
    scan_id = pred_resp.json()["scan_id"]

    # 2. Get scan detail
    detail_resp = client.get(f"/api/v1/history/{scan_id}", headers=headers)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["scan_id"] == scan_id

    # 3. Submit feedback
    fb_payload = {
        "scan_id": scan_id,
        "is_correct": True,
        "true_class": "healthy",
        "comment": "Accurate prediction on fresh leaf sample."
    }
    fb_resp = client.post("/api/v1/feedback", headers=headers, json=fb_payload)
    assert fb_resp.status_code == 201
    assert fb_resp.json()["is_correct"] is True

    # 4. Delete scan
    del_resp = client.delete(f"/api/v1/scans/{scan_id}", headers=headers)
    assert del_resp.status_code == 200
    assert "deleted" in del_resp.json()["detail"].lower()

    # 5. Verify scan is gone
    get_again = client.get(f"/api/v1/history/{scan_id}", headers=headers)
    assert get_again.status_code == 404


def test_health_check_endpoint():
    """Verify /api/v1/health returns ok status and mock mode info."""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["model_mode"] == "mock"


def test_nearest_agro_shops_endpoint():
    """Verify /api/v1/shops returns nearest agro-medical stores with distance."""
    resp = client.get("/api/v1/shops?latitude=16.705&longitude=74.243&district=Kolhapur&limit=3")
    assert resp.status_code == 200
    shops = resp.json()
    assert len(shops) == 3
    assert "name" in shops[0]
    assert "distance_km" in shops[0]
    assert "stocks" in shops[0]
    assert shops[0]["distance_km"] >= 0.0


