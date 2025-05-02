from fastapi.testclient import TestClient
from services.mcp_client.api.main import app

def test_health_check():
    client = TestClient(app)
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
