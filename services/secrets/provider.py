import os
from abc import ABC, abstractmethod
from typing import Optional

class SecretsProvider(ABC):
    """Interfaz para proveedores de secretos."""
    @abstractmethod
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        pass

class EnvSecretsProvider(SecretsProvider):
    """Proveedor de secretos usando variables de entorno."""
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return os.environ.get(key, default)

# Instancia por defecto
secrets = EnvSecretsProvider()
