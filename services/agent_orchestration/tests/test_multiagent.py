from fastapi.testclient import TestClient
from services.agent_orchestration.api.v1 import router as orch_router
from services.mcp_client.api.v1 import router as mcp_router
from fastapi import FastAPI
import pytest

app = FastAPI()
app.include_router(orch_router, prefix="/api/v1")
app.include_router(mcp_router, prefix="/api/v1")
client = TestClient(app)

def test_execute_multiagent_workflow():
    data = {
        "workflow": "demo_multiagente",
        "steps": [
            {"agent": "asistente", "prompt": "Hola, ¿quién eres?", "model": "claude-v1"},
            {"agent": "verificador", "prompt": "Resume la respuesta anterior", "model": "claude-instant-v1"}
        ],
        "input_data": {"usuario": "tause"}
    }
    resp = client.post(
        "/api/v1/workflows/execute",
        json=data,
        headers={"Authorization": "Bearer testtoken"}
    )
    assert resp.status_code == 200
    j = resp.json()
    assert j["success"] is True
    assert j["message"].startswith("Workflow 'demo_multiagente' ejecutado con 2 pasos")
    assert len(j["data"]["steps"]) == 2
    assert j["data"]["steps"][0]["agent"] == "asistente"
    assert j["data"]["steps"][1]["agent"] == "verificador"
    assert j["data"]["input_data"] == {"usuario": "tause"}
