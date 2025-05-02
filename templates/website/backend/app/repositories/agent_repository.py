from typing import List, Optional
from ..schemas.agent import Agent

class AgentRepository:
    """Repositorio de agentes (simulación en memoria)."""
    def __init__(self):
        self._agents = [
            Agent(id=1, name="Claude", status="online"),
            Agent(id=2, name="TauseBot", status="offline")
        ]

    async def get_all(self) -> List[Agent]:
        """Devuelve todos los agentes registrados."""
        return self._agents

    async def get_by_id(self, agent_id: int) -> Optional[Agent]:
        """Devuelve un agente por su ID.
        Args:
            agent_id: ID del agente.
        Returns:
            Instancia de Agent o None si no existe.
        """
        return next((a for a in self._agents if a.id == agent_id), None)
