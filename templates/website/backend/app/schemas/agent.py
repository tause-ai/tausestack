from pydantic import BaseModel, Field
from typing import Optional

class Agent(BaseModel):
    """Modelo de un agente para la API.
    
    Attributes:
        id: Identificador único del agente.
        name: Nombre del agente.
        status: Estado actual del agente.
    """
    id: Optional[int] = Field(None, description="ID único del agente")
    name: str = Field(..., description="Nombre del agente")
    status: str = Field(..., description="Estado del agente (online/offline)")
