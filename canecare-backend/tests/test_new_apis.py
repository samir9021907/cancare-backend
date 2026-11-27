"""
Integration tests for new CaneCare AI endpoints:
- User profile farm fields
- App feedback
- Market rates
- Advisory Q&A
- Notifications
- Recommended products
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_market_rates():
    response = client.get("/api/v1/market/rates")
    assert response.status_code == 200
    data = response.json()
    assert data["national_frp_base_rate"] == 3400.0
    assert len(data["mandis"]) >= 4
    assert data["mandis"][0]["name_mr"] is not None


def test_advisory_questions():
    # 1. List questions
    response = client.get("/api/v1/advisory/questions")
    assert response.status_code == 200
    questions = response.json()
    assert len(questions) >= 3

    # 2. Ask question
    ask_payload = {
        "title": "पाचट कुजवण्यासाठी कोणता जिवाणू संवर्धक वापरावा?",
        "description": "ऊस तुटल्यानंतर शेतात पाचट कुजवण्यासाठी कोणते जिवाणू संवर्धक चांगले आहे?",
        "category": "खत व्यवस्थापन"
    }
    post_res = client.post("/api/v1/advisory/questions", json=ask_payload)
    assert post_res.status_code == 201
    created = post_res.json()
    assert created["title"] == ask_payload["title"]
    assert created["category"] == ask_payload["category"]


def test_notifications():
    response = client.get("/api/v1/notifications")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 4
    assert data["notifications"][0]["title"] is not None


def test_app_feedback():
    feedback_payload = {
        "name": "गणेश जाधव",
        "email": "ganesh.jadhav@example.com",
        "feedback_type": "Report a Bug / Issue",
        "message": "कॅमेरा स्क्रीन छान चालते, पण रात्रीच्या वेळी फ्लॅशचा पर्याय हवा आहे."
    }
    response = client.post("/api/v1/feedback/app", json=feedback_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == feedback_payload["name"]
    assert data["feedback_type"] == feedback_payload["feedback_type"]


def test_recommended_products():
    response = client.get("/api/v1/shops/products?disease=rust")
    assert response.status_code == 200
    data = response.json()
    assert data["disease_id"] == "rust"
    assert len(data["products"]) >= 2
    assert "Mancozeb" in data["products"][0]["name"] or "Propiconazole" in data["products"][0]["name"]
