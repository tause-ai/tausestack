from abc import ABC, abstractmethod
from typing import List
import os
import math

class StorageProvider(ABC):
    """Interfaz para proveedores de almacenamiento con soporte para chunking."""

    @abstractmethod
    def save(self, path: str, data: bytes) -> None:
        pass

    @abstractmethod
    def load(self, path: str) -> bytes:
        pass

    @abstractmethod
    def list(self, prefix: str = "") -> List[str]:
        pass

    @abstractmethod
    def delete(self, path: str) -> None:
        pass

    # Métodos para chunking
    @abstractmethod
    def save_chunk(self, path: str, chunk: bytes, chunk_index: int) -> None:
        """Guarda un chunk numerado de un archivo grande."""
        pass

    @abstractmethod
    def load_chunk(self, path: str, chunk_index: int, chunk_size: int) -> bytes:
        """Carga un chunk específico de un archivo grande."""
        pass

    @abstractmethod
    def get_num_chunks(self, path: str, chunk_size: int) -> int:
        """Devuelve el número total de chunks para un archivo dado y tamaño de chunk."""
        pass

import re

class LocalStorageProvider(StorageProvider):
    """Implementación local de almacenamiento de archivos con soporte para chunking.
    
    Convención de claves/nombres:
    - Solo letras, números, guiones medios/bajos, puntos y barras (subdirectorios).
    - No se permiten rutas absolutas, secuencias '..', ni caracteres especiales peligrosos.
    - Regex: ^[a-zA-Z0-9._\-/]+$
    """
    _key_regex = re.compile(r'^[a-zA-Z0-9._\-/]+$')

    def __init__(self, base_dir: str = "./storage"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _validate_key(self, path: str):
        if not self._key_regex.match(path):
            raise ValueError(f"Clave/nombre de archivo inválido: '{path}'. Debe cumplir la convención regex ^[a-zA-Z0-9._\-/]+$")
        if os.path.isabs(path) or '..' in path:
            raise ValueError(f"No se permiten rutas absolutas ni '..' en claves: '{path}'")

    def save(self, path: str, data: bytes) -> None:
        self._validate_key(path)
        full_path = os.path.join(self.base_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(data)

    def load(self, path: str) -> bytes:
        self._validate_key(path)
        full_path = os.path.join(self.base_dir, path)
        with open(full_path, "rb") as f:
            return f.read()

    def list(self, prefix: str = "") -> List[str]:
        # La validación de prefix es opcional pero recomendable
        if prefix:
            self._validate_key(prefix)
        result = []
        for root, _, files in os.walk(os.path.join(self.base_dir, prefix)):
            for file in files:
                rel_dir = os.path.relpath(root, self.base_dir)
                result.append(os.path.join(rel_dir, file))
        return result

    def delete(self, path: str) -> None:
        self._validate_key(path)
        full_path = os.path.join(self.base_dir, path)
        os.remove(full_path)

    # --- Chunking ---
    def save_chunk(self, path: str, chunk: bytes, chunk_index: int) -> None:
        self._validate_key(path)
        chunk_path = os.path.join(self.base_dir, f"{path}.chunk{chunk_index}")
        os.makedirs(os.path.dirname(chunk_path), exist_ok=True)
        with open(chunk_path, "wb") as f:
            f.write(chunk)

    def load_chunk(self, path: str, chunk_index: int, chunk_size: int) -> bytes:
        self._validate_key(path)
        chunk_path = os.path.join(self.base_dir, f"{path}.chunk{chunk_index}")
        if not os.path.exists(chunk_path):
            raise FileNotFoundError(f"Chunk {chunk_index} de {path} no encontrado")
        with open(chunk_path, "rb") as f:
            return f.read(chunk_size)

    def get_num_chunks(self, path: str, chunk_size: int) -> int:
        self._validate_key(path)
        full_path = os.path.join(self.base_dir, path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Archivo {path} no encontrado")
        file_size = os.path.getsize(full_path)
        return math.ceil(file_size / chunk_size)
