"""
GCSStorageProvider: Proveedor de almacenamiento basado en Google Cloud Storage para Tausestack.

Requiere google-cloud-storage y credenciales de servicio configuradas (variable GOOGLE_APPLICATION_CREDENTIALS).
Incluye validación de claves/nombres alineada a la convención global.
Soporta operaciones CRUD y chunking eficiente para archivos grandes.
"""
import os
import math
import re
from typing import List
from google.cloud import storage
from .provider import StorageProvider

class GCSStorageProvider(StorageProvider):
    _key_regex = re.compile(r'^[a-zA-Z0-9._\-/]+$')

    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    def _validate_key(self, path: str):
        if not self._key_regex.match(path):
            raise ValueError(f"Clave/nombre de archivo inválido: '{path}'. Debe cumplir la convención regex ^[a-zA-Z0-9._\-/]+$")
        if os.path.isabs(path) or '..' in path:
            raise ValueError(f"No se permiten rutas absolutas ni '..' en claves: '{path}'")

    def save(self, path: str, data: bytes) -> None:
        self._validate_key(path)
        blob = self.bucket.blob(path)
        blob.upload_from_string(data)

    def load(self, path: str) -> bytes:
        self._validate_key(path)
        blob = self.bucket.blob(path)
        if not blob.exists():
            raise FileNotFoundError(f"Archivo {path} no encontrado en GCS")
        return blob.download_as_bytes()

    def list(self, prefix: str = "") -> List[str]:
        if prefix:
            self._validate_key(prefix)
        blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)
        return [blob.name for blob in blobs]

    def delete(self, path: str) -> None:
        self._validate_key(path)
        blob = self.bucket.blob(path)
        blob.delete()

    def save_chunk(self, path: str, chunk: bytes, chunk_index: int) -> None:
        self._validate_key(path)
        chunk_key = f"{path}.chunk{chunk_index}"
        blob = self.bucket.blob(chunk_key)
        blob.upload_from_string(chunk)

    def load_chunk(self, path: str, chunk_index: int, chunk_size: int) -> bytes:
        self._validate_key(path)
        chunk_key = f"{path}.chunk{chunk_index}"
        blob = self.bucket.blob(chunk_key)
        if not blob.exists():
            raise FileNotFoundError(f"Chunk {chunk_index} de {path} no encontrado en GCS")
        return blob.download_as_bytes()[:chunk_size]

    def get_num_chunks(self, path: str, chunk_size: int) -> int:
        self._validate_key(path)
        blob = self.bucket.blob(path)
        if not blob.exists():
            raise FileNotFoundError(f"Archivo {path} no encontrado en GCS")
        size = blob.size
        return math.ceil(size / chunk_size)
