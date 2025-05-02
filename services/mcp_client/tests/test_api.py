from fastapi.testclient import TestClient
from services.mcp_client.api.main import app

client = TestClient(app)

def test_health_check():
    resp = client.get("/api/v1/status")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

def test_models_requires_auth():
    # Sin token
    resp = client.get("/api/v1/models")
    assert resp.status_code == 401
    # Con token dummy válido
    resp = client.get("/api/v1/models", headers={"Authorization": "Bearer testtoken"})
    assert resp.status_code == 200
    assert "models" in resp.json()

def test_anthropic_send_requires_auth():
    # Sin token
    resp = client.post("/api/v1/anthropic/send", json={"prompt": "Hola"})
    assert resp.status_code == 401
    # Con token dummy válido
    payload = {"prompt": "Hola Claude!", "model": "claude-v1"}
    resp = client.post("/api/v1/anthropic/send", json=payload, headers={"Authorization": "Bearer testtoken"})
    assert resp.status_code == 200
    assert resp.json()["response"].startswith("Simulación")
