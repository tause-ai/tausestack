import json
import logging

logger = logging.getLogger(__name__)
import os
import shutil # For ensuring valid filenames, though not strictly needed for simple keys
from pathlib import Path
from typing import Any, Dict, Optional

from .base import AbstractJsonStorageBackend

class LocalJsonStorage(AbstractJsonStorageBackend):
    """Stores JSON objects as files in the local filesystem."""

    def __init__(self, base_path: str = ".tausestack_storage/json"):
        """
        Initializes the LocalJsonStorage.

        Args:
            base_path: The root directory where JSON files will be stored.
                       Defaults to '.tausestack_storage/json' relative to the current working directory.
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"LocalJsonStorage initialized with base_path: {self.base_path}")

    def _get_file_path(self, key: str) -> Path:
        """Generates a file path for a given key, ensuring it's a .json file."""
        # Treat key as a relative path.
        # Ensure the final component has a .json suffix.
        path_key = Path(key)
        
        # Add .json suffix if not present or if it's a different suffix
        if path_key.suffix.lower() != ".json":
            path_key = path_key.with_suffix(".json")
            
        # Note: Further sanitization of path components (e.g., for ':' or '\\')
        # could be added here if necessary, applied to each part of path_key.parts.
        return self.base_path / path_key

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        file_path = self._get_file_path(key)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.debug(f"File not found at {file_path} for key '{key}'")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {file_path} for key '{key}': {e}", exc_info=True)
            return None

    def put(self, key: str, value: Dict[str, Any]) -> None:
        file_path = self._get_file_path(key)
        # Ensure parent directory for the key exists if key contains path-like structures
        file_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(value, f, indent=4, ensure_ascii=False)
            logger.debug(f"Successfully wrote JSON to {file_path} for key '{key}'")
        except IOError as e:
            logger.error(f"Error writing JSON to {file_path} for key '{key}': {e}", exc_info=True)
            raise

    def delete(self, key: str) -> None:
        file_path = self._get_file_path(key)
        try:
            os.remove(file_path)
            logger.debug(f"Successfully deleted file {file_path} for key '{key}'")
        except FileNotFoundError:
            logger.debug(f"File not found at {file_path} for key '{key}' during delete operation.")
            pass 
        except OSError as e:
            logger.error(f"Error deleting file {file_path} for key '{key}': {e}", exc_info=True)
            raise


try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    # Allow the module to be imported, but S3JsonStorage will fail at runtime if used.
    # Users will need to install boto3.
    class ClientError(Exception): pass # Define a dummy for type hinting if boto3 is not there

class S3JsonStorage(AbstractJsonStorageBackend):
    """Stores JSON objects in AWS S3."""

    def __init__(self, bucket_name: str, s3_client=None):
        """
        Initializes the S3JsonStorage.

        Args:
            bucket_name: The name of the S3 bucket.
            s3_client: Optional pre-configured boto3 S3 client for testing or specific configurations.
        """
        if not BOTO3_AVAILABLE:
            logger.critical("boto3 is required for S3JsonStorage but is not installed.")
            raise ImportError("boto3 is required for S3JsonStorage. Please install it: pip install boto3")
        
        self.bucket_name = bucket_name
        self.s3_client = s3_client if s3_client else boto3.client('s3')
        logger.debug(f"S3JsonStorage initialized for bucket: {self.bucket_name}. Custom S3 client provided: {s3_client is not None}")

    def _get_s3_key(self, key: str) -> str:
        """Generates an S3 key. Ensures it doesn't start with / and typically ends with .json."""
        # S3 keys should not start with a slash if you want them to behave like regular paths
        s3_key = key.lstrip('/') 
        if not s3_key.endswith(".json"):
            # Append .json if not already, to distinguish JSON files. 
            # This is a convention, adjust if your needs differ.
            s3_key += ".json"
        return s3_key

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        s3_key = self._get_s3_key(key)
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            content = response['Body'].read().decode('utf-8')
            return json.loads(content)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.debug(f"S3 object {s3_key} not found in bucket {self.bucket_name} for key '{key}'")
                return None
            logger.error(f"Error getting S3 object {s3_key} from bucket {self.bucket_name} for key '{key}': {e}", exc_info=True)
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from S3 object {s3_key} for key '{key}': {e}", exc_info=True)
            raise

    def put(self, key: str, value: Dict[str, Any]) -> None:
        s3_key = self._get_s3_key(key)
        try:
            json_string = json.dumps(value, indent=4, ensure_ascii=False)
            self.s3_client.put_object(
                Bucket=self.bucket_name, 
                Key=s3_key, 
                Body=json_string.encode('utf-8'),
                ContentType='application/json'
            )
            logger.debug(f"Successfully put S3 object {s3_key} to bucket {self.bucket_name} for key '{key}'")
        except ClientError as e:
            logger.error(f"Error putting S3 object {s3_key} to bucket {self.bucket_name} for key '{key}': {e}", exc_info=True)
            raise
        except IOError as e: # For issues with encoding or string operations before S3 call
            logger.error(f"IOError before S3 put for key {s3_key}: {e}", exc_info=True)
            raise

    def delete(self, key: str) -> None:
        s3_key = self._get_s3_key(key)
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.debug(f"Successfully deleted S3 object {s3_key} from bucket {self.bucket_name} for key '{key}'")
        except ClientError as e:
            # Log S3 errors. delete_object is idempotent for NoSuchKey.
            # Only raise for other unexpected ClientErrors.
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.debug(f"Attempted to delete non-existent S3 object {s3_key} from bucket {self.bucket_name} for key '{key}'. No action taken.")
            else:
                logger.warning(f"Error deleting S3 object {s3_key} from bucket {self.bucket_name} for key '{key}': {e}", exc_info=True)
                raise # Re-raise unexpected errors
