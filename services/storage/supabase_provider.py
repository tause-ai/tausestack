"""
Adaptador de almacenamiento Supabase para Tausestack.

Implementa la interfaz StorageProvider usando Supabase Storage como backend.
Requiere las librerías oficiales de supabase-py y configuración por variables de entorno o parámetros.
"""

from .provider import StorageProvider
from typing import List
import os
from supabase import create_client, Client

class SupabaseStorageProvider(StorageProvider):
    """
    Proveedor de almacenamiento basado en Supabase Storage.
    """
    def __init__(self, supabase_url: str = None, supabase_key: str = None, bucket: str = "public"):
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY")
        self.bucket = bucket
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Faltan SUPABASE_URL o SUPABASE_KEY para inicializar SupabaseStorageProvider")
        self.client: Client = create_client(self.supabase_url, self.supabase_key)

    def save(self, path: str, data: bytes) -> None:
        res = self.client.storage.from_(self.bucket).upload(path, data, upsert=True)
        if res.get("error"):
            raise RuntimeError(f"Error al guardar archivo en Supabase Storage: {res['error']['message']}")

    def load(self, path: str) -> bytes:
        res = self.client.storage.from_(self.bucket).download(path)
        if hasattr(res, "data") and res.data:
            return res.data
        raise FileNotFoundError(f"No se pudo descargar el archivo {path} de Supabase Storage")

    def list(self, prefix: str = "") -> List[str]:
        res = self.client.storage.from_(self.bucket).list(prefix)
        if res.get("error"):
            raise RuntimeError(f"Error al listar archivos en Supabase Storage: {res['error']['message']}")
        return [item["name"] for item in res.get("data", [])]

    def delete(self, path: str) -> None:
        res = self.client.storage.from_(self.bucket).remove([path])
        if res.get("error"):
            raise RuntimeError(f"Error al eliminar archivo en Supabase Storage: {res['error']['message']}")
