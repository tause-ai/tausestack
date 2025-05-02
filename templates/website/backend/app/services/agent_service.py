from typing import List, Optional
from ..schemas.agent import Agent
from ..repositories.agent_repository import AgentRepository

class AgentService:
    """Servicio para operaciones de agentes."""

    def __init__(self, repository: AgentRepository):
        self.repository = repository

    async def list_agents(self) -> List[Agent]:
        """Obtiene la lista de todos los agentes."""
        return await self.repository.get_all()

    async def get_agent(self, agent_id: int) -> Optional[Agent]:
        """Obtiene un agente por su ID.
        
        Args:
            agent_id: ID del agente.
        Returns:
            Instancia de Agent o None si no existe.
        """
        return await self.repository.get_by_id(agent_id)
