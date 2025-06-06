from typing import Any, Dict, Optional, Type
import logging

logger = logging.getLogger(__name__)
import os

from .base import AbstractJsonStorageBackend
from .backends import LocalJsonStorage, S3JsonStorage

class JsonClient:
    """Client for interacting with JSON storage.

    This client provides a simple interface (get, put, delete) for JSON data,
    delegating the actual storage operations to a configured backend.
    """
    _backend_instance: Optional[AbstractJsonStorageBackend] = None

    def __init__(self, backend_class: Optional[Type[AbstractJsonStorageBackend]] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initializes the JsonClient.

        If backend_class is provided, it will be used. Otherwise, it attempts to determine
        the backend from configuration (not yet implemented, defaults to LocalJsonStorage).

        Args:
            backend_class: The specific backend class to use (e.g., LocalJsonStorage).
            config: Configuration dictionary for the backend (e.g., {'base_path': '/tmp/storage'}).
        """
        if JsonClient._backend_instance is None:
            logger.debug("Attempting to initialize storage backend for JsonClient.")
            resolved_config = config or {}
            if backend_class:
                # If a specific backend class is provided, use it.
                # This is useful for testing or specific overrides.
                if backend_class == LocalJsonStorage and 'base_path' not in resolved_config:
                    # Provide default base_path if not in config for LocalJsonStorage
                    resolved_config['base_path'] = os.getenv('TAUSESTACK_LOCAL_STORAGE_PATH', '.tausestack_storage/json')
                JsonClient._backend_instance = backend_class(**resolved_config)
                logger.info(f"JsonClient initialized with explicitly provided backend: {backend_class.__name__} using config: {resolved_config}")
            else:
                # TODO: Implement configuration-based backend selection
                # For now, defaults to LocalJsonStorage
                # In the future, read TAUSESTACK_STORAGE_BACKEND env var
                # and instantiate S3JsonStorage or LocalJsonStorage accordingly.
                storage_backend_type = os.getenv('TAUSESTACK_STORAGE_BACKEND', 'local')
                
                if storage_backend_type == 'local':
                    base_path = resolved_config.get('base_path', 
                                                os.getenv('TAUSESTACK_LOCAL_STORAGE_PATH', '.tausestack_storage/json'))
                    JsonClient._backend_instance = LocalJsonStorage(base_path=base_path)
                    logger.info(f"JsonClient initialized with LocalJsonStorage. Backend type: 'local', base_path: '{base_path}'")
                elif storage_backend_type == 's3':
                    bucket_name = resolved_config.get('bucket_name', os.getenv('TAUSESTACK_S3_BUCKET_NAME'))
                    if not bucket_name:
                        # Try to get it from a more general AWS_S3_BUCKET_NAME if specific one is not set
                        bucket_name = os.getenv('AWS_S3_BUCKET_NAME') 
                    if not bucket_name:
                        logger.error("S3 bucket name not configured. TAUSESTACK_S3_BUCKET_NAME or AWS_S3_BUCKET_NAME must be set for 's3' backend.")
                        raise ValueError("S3 bucket name not configured. Set TAUSESTACK_S3_BUCKET_NAME or AWS_S3_BUCKET_NAME.")
                    try:
                        JsonClient._backend_instance = S3JsonStorage(bucket_name=bucket_name)
                        logger.info(f"JsonClient initialized with S3JsonStorage. Backend type: 's3', bucket_name: '{bucket_name}'")
                    except ImportError as e:
                        logger.critical(f"Failed to initialize S3JsonStorage due to ImportError (likely missing boto3): {e}", exc_info=True)
                        # S3JsonStorage already logs critical if BOTO3_AVAILABLE is False, this adds context from main.py
                        raise ImportError(f"{e} Ensure boto3 is installed for S3 support: pip install boto3") from e
                else:
                    logger.error(f"Unsupported storage backend type specified: '{storage_backend_type}'. Supported types are 'local', 's3'.")
                    raise ValueError(f"Unsupported storage backend type: {storage_backend_type}. Supported types are 'local', 's3'.")
        
        # Ensure the instance is not None after initialization attempt
        if JsonClient._backend_instance is None:
            logger.critical("Storage backend could not be initialized after attempting all configuration paths.")
            raise RuntimeError("Storage backend could not be initialized.")

        self._backend = JsonClient._backend_instance

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieves a JSON object by key from the configured backend."""
        return self._backend.get(key)

    def put(self, key: str, value: Dict[str, Any]) -> None:
        """Stores a JSON object by key in the configured backend."""
        self._backend.put(key, value)

    def delete(self, key: str) -> None:
        """Deletes a JSON object by key from the configured backend."""
        self._backend.delete(key)

# Global instance for convenience, similar to how Databutton SDK might expose it.
# This instance will be initialized with default settings (LocalJsonStorage for now).
# Users can also create their own JsonClient instances with specific backends/configs if needed.
json_client = JsonClient()
