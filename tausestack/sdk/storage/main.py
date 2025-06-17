import logging
import os
from typing import Any, Dict, Optional, Union

from .backends import LocalStorage, S3Storage, BOTO3_AVAILABLE
from .base import AbstractJsonStorageBackend, AbstractBinaryStorageBackend

logger = logging.getLogger(__name__)

# --- Client Classes ---

class JsonStorageClient:
    """
    A client for interacting with the configured JSON storage backend.
    """
    def __init__(self, backend: AbstractJsonStorageBackend):
        self._backend = backend
        logger.debug(f"JsonStorageClient initialized with backend: {type(backend).__name__}")

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a JSON object from the storage by its key.
        """
        return self._backend.get_json(key)

    def put(self, key: str, value: Dict[str, Any]) -> None:
        """
        Saves or updates a JSON object in the storage.
        """
        self._backend.put_json(key, value)

    def delete(self, key: str) -> None:
        """
        Deletes a JSON object from the storage by its key.
        """
        self._backend.delete_json(key)

class BinaryStorageClient:
    """
    A client for interacting with the configured binary storage backend.
    """
    def __init__(self, backend: AbstractBinaryStorageBackend):
        self._backend = backend
        logger.debug(f"BinaryStorageClient initialized with backend: {type(backend).__name__}")

    def get(self, key: str) -> Optional[bytes]:
        """
        Retrieves a binary object from the storage by its key.
        """
        return self._backend.get_binary(key)

    def put(self, key: str, value: bytes, content_type: Optional[str] = None) -> None:
        """
        Saves or updates a binary object in the storage.
        """
        self._backend.put_binary(key, value, content_type)

    def delete(self, key: str) -> None:
        """
        Deletes a binary object from the storage by its key.
        """
        self._backend.delete_binary(key)

# --- Backend Factory and Singleton ---

StorageBackend = Union[AbstractJsonStorageBackend, AbstractBinaryStorageBackend]
_storage_backend_instance: Optional[StorageBackend] = None

def _get_storage_backend() -> StorageBackend:
    """
    Factory function to create and return the appropriate storage backend
    based on environment variables.
    """
    backend_type = os.environ.get("TAUSESTACK_STORAGE_BACKEND", "local").lower()
    logger.info(f"Selected storage backend: {backend_type}")

    if backend_type == "local":
        json_path = os.environ.get("TAUSESTACK_LOCAL_JSON_STORAGE_PATH", ".tausestack_storage/json")
        binary_path = os.environ.get("TAUSESTACK_LOCAL_BINARY_STORAGE_PATH", ".tausestack_storage/binary")
        return LocalStorage(base_json_path=json_path, base_binary_path=binary_path)
    
    elif backend_type == "s3":
        if not BOTO3_AVAILABLE:
            raise ImportError("TAUSESTACK_STORAGE_BACKEND is 's3', but boto3 is not installed. Please run 'pip install boto3'.")
        
        bucket_name = os.environ.get("TAUSESTACK_S3_BUCKET_NAME")
        if not bucket_name:
            raise ValueError("TAUSESTACK_STORAGE_BACKEND is 's3', but TAUSESTACK_S3_BUCKET_NAME is not set.")
        
        return S3Storage(bucket_name=bucket_name)

    else:
        raise ValueError(f"Unknown storage backend: '{backend_type}'. Supported backends are 'local' and 's3'.")

def _get_backend_instance() -> StorageBackend:
    """Lazy initializer for the backend singleton."""
    global _storage_backend_instance
    if _storage_backend_instance is None:
        _storage_backend_instance = _get_storage_backend()
    return _storage_backend_instance

# --- Client Instances ---
# These instances use the lazily initialized backend singleton.
# The type ignore is used because _get_backend_instance returns a Union, 
# but LocalStorage and S3Storage implement both AbstractJsonStorageBackend and AbstractBinaryStorageBackend.
_initialized_backend = _get_backend_instance()
json_client = JsonStorageClient(backend=_initialized_backend) # type: ignore
binary_client = BinaryStorageClient(backend=_initialized_backend) # type: ignore

# --- Public API ---

# The public client instances that applications will import and use.
_backend = _get_backend_instance()
json = JsonStorageClient(backend=_backend)
binary = BinaryStorageClient(backend=_backend)
