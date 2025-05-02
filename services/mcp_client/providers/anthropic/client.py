import httpx
from typing import Any, Dict, List, Optional
from ...core.base_client import BaseMCPClient
from ...core.base_message import MCPMessage, MCPBatchRequest, MCPBatchResponse
from ...core.exceptions import MCPProviderError

class AnthropicMCPClient(BaseMCPClient):
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

    @property
    def supported_models(self) -> List[str]:
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3-5-sonnet-20240620",
            "claude-3-7-sonnet-20250219"
        ]
