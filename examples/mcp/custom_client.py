"""
Ejemplo de cómo implementar un cliente MCP personalizado utilizando
la interfaz MCPClient del framework Tausestack.
"""

import httpx
from typing import Any, Dict, List, Optional
from services.mcp_client.interfaces.mcp_client import MCPClient
from services.mcp_client.interfaces.mcp_message import MCPMessage, MCPBatchRequest, MCPBatchResponse
from services.mcp_client.interfaces.exceptions import MCPProviderError

class CustomMCPClient(MCPClient):
    """
    Cliente MCP personalizado que implementa la interfaz MCPClient.
    Este es un ejemplo de cómo crear tu propio adaptador para un proveedor específico.
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.ejemplo.com", **kwargs):
        super().__init__(api_key, **kwargs)
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Inicializa el cliente con la configuración proporcionada."""
        try:
            if "api_key" in config:
                self.api_key = config["api_key"]
                self.client.headers.update({"Authorization": f"Bearer {self.api_key}"})
            if "base_url" in config:
                self.base_url = config["base_url"]
            return True
        except Exception:
            return False
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """Obtiene las herramientas disponibles en la API del proveedor."""
        try:
            response = await self.client.get(f"{self.base_url}/tools")
            response.raise_for_status()
            return response.json().get("tools", [])
        except Exception as e:
            raise MCPProviderError(f"Error al listar herramientas: {e}")
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Llama a una herramienta específica en la API del proveedor."""
        try:
            response = await self.client.post(
                f"{self.base_url}/tools/{tool_name}/call",
                json=params
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise MCPProviderError(f"Error al llamar a la herramienta {tool_name}: {e}")
    
    async def get_manifest(self) -> Dict[str, Any]:
        """Obtiene el manifiesto del servidor."""
        try:
            response = await self.client.get(f"{self.base_url}/manifest")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise MCPProviderError(f"Error al obtener manifiesto: {e}")
    
    async def send_message(self, message: MCPMessage) -> Any:
        """Envía un mensaje al proveedor y devuelve la respuesta."""
        try:
            response = await self.client.post(
                f"{self.base_url}/messages",
                json=message.dict(exclude_none=True)
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise MCPProviderError(f"Error al enviar mensaje: {e}")
    
    async def send_batch(self, batch: MCPBatchRequest) -> MCPBatchResponse:
        """Envía un batch de mensajes al proveedor."""
        try:
            response = await self.client.post(
                f"{self.base_url}/messages/batch",
                json=batch.dict(exclude_none=True)
            )
            response.raise_for_status()
            data = response.json()
            return MCPBatchResponse(results=data.get("results", []), raw_response=data)
        except Exception as e:
            raise MCPProviderError(f"Error al enviar batch: {e}")
    
    async def close(self):
        """Cierra conexiones y recursos del cliente."""
        await self.client.aclose()
    
    @property
    def supported_models(self) -> List[str]:
        """Lista de modelos soportados por este cliente."""
        return ["modelo-basico", "modelo-avanzado"]


# Ejemplo de uso
async def ejemplo_uso():
    # Inicializar cliente
    client = CustomMCPClient(api_key="tu-api-key")
    
    # Configurar cliente
    await client.initialize({
        "base_url": "https://otro-api.ejemplo.com"
    })
    
    # Listar herramientas disponibles
    tools = await client.list_tools()
    print(f"Herramientas disponibles: {tools}")
    
    # Crear y enviar un mensaje
    message = MCPMessage(
        role="user",
        content="Hola, necesito ayuda con mi proyecto"
    )
    response = await client.send_message(message)
    print(f"Respuesta: {response}")
    
    # Cerrar cliente
    await client.close()
