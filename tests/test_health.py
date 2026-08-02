from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_top_level_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["app"] == "CareerFlow AI"
    assert "version" in data


def test_api_v1_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["app"] == "CareerFlow AI"
