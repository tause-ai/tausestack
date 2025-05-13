import httpx
from typing import Any, Dict, List, Optional
from ...interfaces.mcp_client import MCPClient
from ...interfaces.mcp_message import MCPMessage, MCPBatchRequest, MCPBatchResponse
from ...interfaces.exceptions import MCPProviderError

class AnthropicMCPClient(MCPClient):
    """Cliente MCP para Claude (Anthropic) siguiendo el protocolo MCP."""
    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com", **kwargs):
        super().__init__(api_key, **kwargs)
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        )

    async def send_message(self, message: MCPMessage) -> Any:
        # Implementación mínima: envía un mensaje MCP como /v1/messages
        try:
            response = await self.client.post(
                f"{self.base_url}/v1/messages",
                json=message.dict(exclude_none=True)
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise MCPProviderError(f"Error enviando mensaje a Anthropic MCP: {e}")

    async def send_batch(self, batch: MCPBatchRequest) -> MCPBatchResponse:
        # Implementación mínima: envía un batch de mensajes MCP
        try:
            response = await self.client.post(
                f"{self.base_url}/v1/messages:batch",
                json=batch.dict(exclude_none=True)
            )
            response.raise_for_status()
            data = response.json()
            return MCPBatchResponse(results=data.get("results", []), raw_response=data)
        except Exception as e:
            raise MCPProviderError(f"Error enviando batch a Anthropic MCP: {e}")

    async def close(self):
        await self.client.aclose()

    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Inicializa el cliente con la configuración proporcionada."""
        try:
            if "api_key" in config:
                self.api_key = config["api_key"]
                self.client.headers.update({"x-api-key": self.api_key})
            if "base_url" in config:
                self.base_url = config["base_url"]
            return True
        except Exception:
            return False
            
    async def list_tools(self) -> List[Dict[str, Any]]:
        """Obtiene las herramientas disponibles en la API de Anthropic."""
        # Anthropic no tiene un endpoint específico para listar tools
        # Usualmente se definen en la request, así que devolvemos una lista vacía
        return []
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Llama a una herramienta específica en la API de Anthropic."""
        # Anthropic no soporta llamadas directas a tools, se envían como parte del mensaje
        raise NotImplementedError("Anthropic no soporta llamadas directas a tools")
    
    async def get_manifest(self) -> Dict[str, Any]:
        """Obtiene el manifiesto de la API de Anthropic."""
        # Anthropic no tiene un manifest específico como otros proveedores MCP
        return {
            "provider": "anthropic",
            "models": self.supported_models,
            "capabilities": ["chat", "tools"]
        }
    
    @property
    def supported_models(self) -> List[str]:
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3-5-sonnet-20240620",
            "claude-3-7-sonnet-20250219"
        ]
