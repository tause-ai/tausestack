"""
VaultSecretsProvider: Proveedor de secretos basado en HashiCorp Vault para Tausestack.

Requiere la librería 'hvac' y configuración de URL/token de Vault.
Incluye patrón seguro y desacoplado, alineado a la convención global.
"""
import os
from typing import Optional
import hvac
from .provider import SecretsProvider

class VaultSecretsProvider(SecretsProvider):
    def __init__(self, vault_url: str = None, token: str = None, mount_point: str = "secret"):
        self.vault_url = vault_url or os.getenv("VAULT_URL")
        self.token = token or os.getenv("VAULT_TOKEN")
        self.mount_point = mount_point
        if not self.vault_url or not self.token:
            raise ValueError("Faltan VAULT_URL o VAULT_TOKEN para inicializar VaultSecretsProvider")
        self.client = hvac.Client(url=self.vault_url, token=self.token)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        try:
            read_response = self.client.secrets.kv.v2.read_secret_version(
                path=key, mount_point=self.mount_point
            )
            data = read_response["data"]["data"]
            return data.get("value", default)
        except Exception:
            return default
