from fastapi import FastAPI, Depends, HTTPException
from typing import List
from .schemas.agent import Agent
from .services.agent_service import AgentService
from .repositories.agent_repository import AgentRepository

app = FastAPI()

# Inyección de dependencias
repo = AgentRepository()
service = AgentService(repo)

@app.get("/", tags=["root"])
def read_root() -> dict:
    """Endpoint raíz de bienvenida."""
    return {"message": "¡Bienvenido a tu API FastAPI con TauseStack!"}

@app.get("/agents", response_model=List[Agent], tags=["agents"])
async def list_agents() -> List[Agent]:
    """Devuelve la lista de todos los agentes registrados."""
    return await service.list_agents()

@app.get("/agents/{agent_id}", response_model=Agent, tags=["agents"])
async def get_agent(agent_id: int) -> Agent:
    """Devuelve un agente por su ID.
    Args:
        agent_id: ID del agente.
    Returns:
        Agent encontrado.
    Raises:
        HTTPException: Si el agente no existe.
    """
    agent = await service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    return agent
