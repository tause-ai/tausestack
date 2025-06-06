"""
Proveedor de secretos basado en Supabase para TauseStack.
Permite obtener secretos desde una tabla segura en Supabase, con fallback opcional a entorno.
"""
from .provider import SecretsProvider
from typing import Optional
import os
from supabase import create_client, Client

class SupabaseSecretsProvider(SecretsProvider):
    """
    Proveedor de secretos usando Supabase (tabla 'secrets').
    Si no se encuentra el secreto, puede hacer fallback a entorno.
    """
    def __init__(self, supabase_url: str = None, supabase_key: str = None, fallback_env: bool = True):
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY")
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Faltan SUPABASE_URL o SUPABASE_KEY para inicializar SupabaseSecretsProvider")
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        self.fallback_env = fallback_env

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        # Busca el secreto en la tabla 'secrets' (campos: key, value)
        res = self.client.table("secrets").select("value").eq("key", key).limit(1).execute()
        data = getattr(res, "data", None)
        if data and len(data) > 0 and "value" in data[0]:
            return data[0]["value"]
        if self.fallback_env:
            import os
            return os.environ.get(key, default)
        return default
