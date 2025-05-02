from typing import Dict, Type, Optional
from .base_client import BaseMCPClient

class MCPRegistry:
    """Registro global de proveedores MCP disponibles."""
    _providers: Dict[str, Type[BaseMCPClient]] = {}

    @classmethod
    def register(cls, name: str, provider_class: Type[BaseMCPClient]) -> None:
        cls._providers[name] = provider_class

    @classmethod
    def get_provider(cls, name: str) -> Optional[Type[BaseMCPClient]]:
        return cls._providers.get(name)

    @classmethod
    def list_providers(cls) -> Dict[str, Type[BaseMCPClient]]:
        return cls._providers.copy()
