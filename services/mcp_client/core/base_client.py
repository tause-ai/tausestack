from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from .base_message import MCPMessage, MCPBatchRequest, MCPBatchResponse

class BaseMCPClient(ABC):
    """Interfaz abstracta para todos los clientes MCP."""

    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.provider_name = self.__class__.__name__
        self.config = kwargs

    @abstractmethod
    async def send_message(self, message: MCPMessage) -> Any:
        """Envía un mensaje MCP y devuelve la respuesta."""
        pass

    @abstractmethod
    async def send_batch(self, batch: MCPBatchRequest) -> MCPBatchResponse:
        """Envía un batch de mensajes MCP y devuelve la respuesta."""
        pass

    @abstractmethod
    async def close(self):
        """Cierra conexiones y recursos del cliente."""
        pass

    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        pass
