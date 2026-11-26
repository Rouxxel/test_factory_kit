from app.config import settings
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_returns_ok_and_model():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "model": settings.MODEL_NAME}
