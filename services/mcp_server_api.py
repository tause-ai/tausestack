"""
API para el servidor MCP Tause: gestión de memoria/contexto y tools para orquestación multiagente.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

app = FastAPI(title="MCP Tause Server", description="Servidor MCP para memoria y tools avanzada")

# --- Modelos ---

class AgentMemory(BaseModel):
    agent_id: str = Field(...)
    context: Dict[str, Any] = Field(default_factory=dict)

class ToolRegistration(BaseModel):
    tool_id: str = Field(...)
    name: str
    description: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)

# --- Almacenamiento en memoria (MVP) ---
import json
from pathlib import Path

AGENT_MEMORIES: Dict[str, AgentMemory] = {}
TOOLS: Dict[str, ToolRegistration] = {}

# --- Persistencia simple (archivo JSON) ---
DATA_PATH = Path(__file__).parent / "mcp_data.json"

def save_data():
    data = {
        "agent_memories": {k: v.dict() for k, v in AGENT_MEMORIES.items()},
        "tools": {k: v.dict() for k, v in TOOLS.items()},
    }
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)

def load_data():
    if DATA_PATH.exists():
        with open(DATA_PATH) as f:
            data = json.load(f)
        AGENT_MEMORIES.clear()
        TOOLS.clear()
        for k, v in data.get("agent_memories", {}).items():
            AGENT_MEMORIES[k] = AgentMemory(**v)
        for k, v in data.get("tools", {}).items():
            TOOLS[k] = ToolRegistration(**v)

# Cargar datos al iniciar
load_data()

# --- Endpoints ---

@app.get("/memory/all")
def get_all_memories():
    """
    Expone todas las memorias de agentes en formato federable.
    """
    return {"memories": [mem.dict() for mem in AGENT_MEMORIES.values()]}

from fastapi import Body, Request
import httpx
from core.utils.auth import require_jwt, is_peer_allowed
import logging

@app.post("/federation/memory/pull")
@require_jwt
def pull_federated_memory(request: Request, payload: dict = Body(...)):
    """
    Sincroniza la memoria de agentes desde un MCP remoto.
    Payload: {"url": str, "token": str (opcional)}
    """
    url = payload.get("url")
    token = payload.get("token")
    if not url:
        raise HTTPException(status_code=400, detail="URL remota requerida")
    if not is_peer_allowed(url):
        raise HTTPException(status_code=403, detail="Peer remoto no permitido")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = httpx.get(f"{url}/memory/all", headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        count = 0
        for mem in data.get("memories", []):
            agent_id = mem.get("agent_id")
            context = mem.get("context", {})
            if agent_id:
                AGENT_MEMORIES[agent_id] = AgentMemory(agent_id=agent_id, context=context)
                count += 1
        save_data()
        logging.info(f"Federación memoria desde {url} exitosa: {count} memorias importadas")
        return {"status": "ok", "imported": count}
    except Exception as e:
        logging.error(f"Federación memoria desde {url} fallida: {e}")
        raise HTTPException(status_code=502, detail=f"Error federando memoria: {e}")

@app.post("/federation/tools/pull")
@require_jwt
def pull_federated_tools(request: Request, payload: dict = Body(...)):
    """
    Sincroniza tools desde un MCP remoto.
    Payload: {"url": str, "token": str (opcional)}
    """
    url = payload.get("url")
    token = payload.get("token")
    if not url:
        raise HTTPException(status_code=400, detail="URL remota requerida")
    if not is_peer_allowed(url):
        raise HTTPException(status_code=403, detail="Peer remoto no permitido")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = httpx.get(f"{url}/tools", headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        count = 0
        for tool in data:
            tool_id = tool.get("tool_id")
            if tool_id:
                TOOLS[tool_id] = ToolRegistration(**tool)
                count += 1
        save_data()
        logging.info(f"Federación tools desde {url} exitosa: {count} tools importados")
        return {"status": "ok", "imported": count}
    except Exception as e:
        logging.error(f"Federación tools desde {url} fallida: {e}")
        raise HTTPException(status_code=502, detail=f"Error federando tools: {e}")

@app.post("/memory/register", response_model=AgentMemory)
def register_memory(mem: AgentMemory):
    AGENT_MEMORIES[mem.agent_id] = mem
    save_data()
    return mem

@app.get("/memory/{agent_id}", response_model=AgentMemory)
def get_memory(agent_id: str):
    mem = AGENT_MEMORIES.get(agent_id)
    if not mem:
        raise HTTPException(status_code=404, detail="Agent memory not found")
    return mem

@app.post("/tools/register", response_model=ToolRegistration)
def register_tool(tool: ToolRegistration):
    TOOLS[tool.tool_id] = tool
    save_data()
    return tool

@app.get("/tools", response_model=List[ToolRegistration])
def list_tools():
    return list(TOOLS.values())

@app.get("/tools/{tool_id}", response_model=ToolRegistration)
def get_tool(tool_id: str):
    tool = TOOLS.get(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool
