from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from .mcp_message import MCPMessage, MCPBatchRequest, MCPBatchResponse

class MCPClient(ABC):
    """
    Interfaz abstracta para clientes MCP (Multi-Call Protocol).
    
    Esta clase define el contrato que todos los adaptadores de cliente MCP deben implementar,
    independientemente del proveedor específico (Anthropic, OpenAI, etc).
    """
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Inicializa un cliente MCP con credenciales opcionales.
        
        Args:
            api_key (Optional[str]): API key para autenticación con el proveedor.
            **kwargs: Argumentos adicionales de configuración.
        """
        self.api_key = api_key
        self.provider_name = self.__class__.__name__
        self.config = kwargs
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Inicializa el cliente MCP con la configuración proporcionada.
        
        Args:
            config (Dict[str, Any]): Configuración específica del proveedor.
            
        Returns:
            bool: True si la inicialización fue exitosa, False en caso contrario.
        """
        pass
    
    @abstractmethod
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de herramientas disponibles en el servidor MCP.
        
        Returns:
            List[Dict[str, Any]]: Lista de herramientas disponibles.
        """
        pass
    
    @abstractmethod
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Realiza una llamada a una herramienta específica del servidor MCP.
        
        Args:
            tool_name (str): Nombre de la herramienta a llamar.
            params (Dict[str, Any]): Parámetros para la llamada.
            
        Returns:
            Dict[str, Any]: Respuesta de la llamada a la herramienta.
        """
        pass
    
    @abstractmethod
    async def get_manifest(self) -> Dict[str, Any]:
        """
        Obtiene el manifiesto del servidor MCP.
        
        Returns:
            Dict[str, Any]: Manifiesto del servidor MCP.
        """
        pass

    @abstractmethod
    async def send_message(self, message: MCPMessage) -> Any:
        """
        Envía un mensaje MCP al proveedor y devuelve la respuesta.
        
        Args:
            message (MCPMessage): Mensaje con formato MCP estándar.
            
        Returns:
            Any: Respuesta del proveedor.
        """
        pass

    @abstractmethod
    async def send_batch(self, batch: MCPBatchRequest) -> MCPBatchResponse:
        """
        Envía un batch de mensajes MCP y devuelve la respuesta.
        
        Args:
            batch (MCPBatchRequest): Batch de mensajes a procesar.
            
        Returns:
            MCPBatchResponse: Respuesta del batch.
        """
        pass
        
    @abstractmethod
    async def close(self):
        """
        Cierra conexiones y recursos del cliente.
        """
        pass
        
    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """
        Lista de modelos soportados por este cliente MCP.
        
        Returns:
            List[str]: Lista de identificadores de modelos.
        """
        pass
