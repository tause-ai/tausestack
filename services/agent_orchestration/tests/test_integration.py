from fastapi.testclient import TestClient
from services.agent_orchestration.api.v1 import router as orch_router
from services.mcp_client.api.v1 import router as mcp_router
from fastapi import FastAPI
import pytest

# Montar ambos routers en la misma app para pruebas locales
app = FastAPI()
app.include_router(orch_router, prefix="/api/v1")
app.include_router(mcp_router, prefix="/api/v1")
client = TestClient(app)

def test_execute_workflow_integration():
    data = {
        "workflow": "consulta_claude",
        "input_data": {"prompt": "¿Quién eres?", "model": "claude-v1"}
    }
    resp = client.post(
        "/api/v1/workflows/execute",
        json=data,
        headers={"Authorization": "Bearer testtoken"}
    )
    assert resp.status_code == 200
    j = resp.json()
    assert j["success"] is True
    assert "mcp_response" in j["data"]
    assert j["data"]["mcp_response"]["model"] == "claude-v1"
    assert j["data"]["mcp_response"]["prompt"] == "¿Quién eres?"
    assert "Claude" in j["data"]["mcp_response"]["response"]
    assert j["data"]["input"] == {"prompt": "¿Quién eres?", "model": "claude-v1"}
