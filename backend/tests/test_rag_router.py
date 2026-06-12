from fastapi.testclient import TestClient

from main import app


def test_health_endpoint():
    client = TestClient(app)
    resp = client.get("/api/v1/rag/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
