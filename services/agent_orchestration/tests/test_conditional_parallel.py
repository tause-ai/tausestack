from fastapi.testclient import TestClient
from services.agent_orchestration.api.v1 import router as orch_router
from services.mcp_client.api.v1 import router as mcp_router
from fastapi import FastAPI
import pytest

app = FastAPI()
app.include_router(orch_router, prefix="/api/v1")
app.include_router(mcp_router, prefix="/api/v1")
client = TestClient(app)

def test_conditional_and_parallel_workflow():
    data = {
        "workflow": "demo_condicional_paralelo",
        "steps": [
            {"agent": "a1", "prompt": "¿Eres mayor de edad?", "model": "claude-v1"},
            {"agent": "a2", "prompt": "¿Cuál es tu país?", "model": "claude-v1", "parallel_group": "geo"},
            {"agent": "a3", "prompt": "¿Cuál es tu ocupación?", "model": "claude-v1", "parallel_group": "geo"},
            {"agent": "a4", "prompt": "Solo si país es Colombia", "condition": "steps[1]['output']['response'] == 'Colombia'"}
        ]
    }
    resp = client.post(
        "/api/v1/workflows/execute",
        json=data,
        headers={"Authorization": "Bearer testtoken"}
    )
    assert resp.status_code == 200
    j = resp.json()
    assert j["success"] is True
    assert j["message"].startswith("Workflow 'demo_condicional_paralelo' ejecutado")
    steps = j["data"]["steps"]
    assert len(steps) == 4
    # Paso 1 ejecutado
    assert steps[0]["agent"] == "a1"
    assert "output" in steps[0]
    # Paso 2 y 3 ejecutados en paralelo (ambos tienen output)
    assert steps[1]["agent"] == "a2"
    assert steps[2]["agent"] == "a3"
    assert "output" in steps[1]
    assert "output" in steps[2]
    # Paso 4 omitido por condición
    assert steps[3]["agent"] == "a4"
    assert steps[3]["skipped"] is True
    assert "Condición no satisfecha" in steps[3]["reason"]
