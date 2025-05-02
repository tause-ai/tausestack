from fastapi.testclient import TestClient
from services.agent_orchestration.api.v1 import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router, prefix="/api/v1")
client = TestClient(app)

def test_health_check():
    resp = client.get("/api/v1/status")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

def test_execute_workflow_requires_auth():
    data = {"workflow": "demo", "input_data": {"foo": "bar"}}
    # Sin token
    resp = client.post("/api/v1/workflows/execute", json=data)
    assert resp.status_code == 401
    # Con token dummy válido
    resp = client.post("/api/v1/workflows/execute", json=data, headers={"Authorization": "Bearer testtoken"})
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert resp.json()["message"].startswith("Workflow")
