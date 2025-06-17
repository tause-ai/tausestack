import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from .base import AbstractJsonStorageBackend, AbstractBinaryStorageBackend

logger = logging.getLogger(__name__)

class LocalStorage(AbstractJsonStorageBackend, AbstractBinaryStorageBackend):
    """Stores JSON objects and binary files in the local filesystem."""

    def __init__(self, base_json_path: str = ".tausestack_storage/json", base_binary_path: str = ".tausestack_storage/binary"):
        self.base_json_path = Path(base_json_path)
        self.base_binary_path = Path(base_binary_path)
        self.base_json_path.mkdir(parents=True, exist_ok=True)
        self.base_binary_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"LocalStorage initialized. JSON path: {self.base_json_path}, Binary path: {self.base_binary_path}")

    # --- JSON Methods --- 
    def _get_json_file_path(self, key: str) -> Path:
        path_key = Path(key)
        if path_key.suffix.lower() != ".json":
            path_key = path_key.with_suffix(".json")
        return self.base_json_path / path_key

    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        file_path = self._get_json_file_path(key)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.debug(f"JSON file not found at {file_path} for key '{key}'")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {file_path} for key '{key}': {e}", exc_info=True)
            return None # Or re-raise as a custom storage exception

    def put_json(self, key: str, value: Dict[str, Any]) -> None:
        file_path = self._get_json_file_path(key)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(value, f, indent=4, ensure_ascii=False)
            logger.debug(f"Successfully wrote JSON to {file_path} for key '{key}'")
        except IOError as e:
            logger.error(f"Error writing JSON to {file_path} for key '{key}': {e}", exc_info=True)
            raise

    def delete_json(self, key: str) -> None:
        file_path = self._get_json_file_path(key)
        try:
            os.remove(file_path)
            logger.debug(f"Successfully deleted JSON file {file_path} for key '{key}'")
        except FileNotFoundError:
            logger.debug(f"JSON file not found at {file_path} for key '{key}' during delete.")
            pass 
        except OSError as e:
            logger.error(f"Error deleting JSON file {file_path} for key '{key}': {e}", exc_info=True)
            raise

    # --- Binary Methods --- 
    def _get_binary_file_path(self, key: str) -> Path:
        # For binary files, use the key as is, without assuming/adding extensions.
        # The key should represent the intended filename or path relative to base_binary_path.
        return self.base_binary_path / Path(key)

    def get_binary(self, key: str) -> Optional[bytes]:
        file_path = self._get_binary_file_path(key)
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            logger.debug(f"Binary file not found at {file_path} for key '{key}'")
            return None
        except IOError as e:
            logger.error(f"Error reading binary file {file_path} for key '{key}': {e}", exc_info=True)
            raise

    def put_binary(self, key: str, value: bytes, content_type: Optional[str] = None) -> None:
        # content_type is ignored for local storage but kept for interface consistency
        file_path = self._get_binary_file_path(key)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(file_path, 'wb') as f:
                f.write(value)
            logger.debug(f"Successfully wrote binary data to {file_path} for key '{key}'")
        except IOError as e:
            logger.error(f"Error writing binary data to {file_path} for key '{key}': {e}", exc_info=True)
            raise

    def delete_binary(self, key: str) -> None:
        file_path = self._get_binary_file_path(key)
        try:
            os.remove(file_path)
            logger.debug(f"Successfully deleted binary file {file_path} for key '{key}'")
        except FileNotFoundError:
            logger.debug(f"Binary file not found at {file_path} for key '{key}' during delete.")
            pass
        except OSError as e:
            logger.error(f"Error deleting binary file {file_path} for key '{key}': {e}", exc_info=True)
            raise

# --- S3 Storage --- 
try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    class ClientError(Exception): pass # Dummy for type hinting if boto3 not available

class S3Storage(AbstractJsonStorageBackend, AbstractBinaryStorageBackend):
    """Stores JSON objects and binary files in AWS S3."""

    def __init__(self, bucket_name: str, s3_client=None):
        if not BOTO3_AVAILABLE:
            logger.critical("boto3 is required for S3Storage but is not installed.")
            raise ImportError("boto3 is required for S3Storage. Please install it: pip install boto3")
        
        self.bucket_name = bucket_name
        self.s3_client = s3_client if s3_client else boto3.client('s3')
        logger.debug(f"S3Storage initialized for bucket: {self.bucket_name}. Custom S3 client: {s3_client is not None}")

    # --- JSON Methods --- 
    def _get_json_s3_key(self, key: str) -> str:
        s3_key = key.lstrip('/') 
        if not s3_key.endswith(".json"):
            s3_key += ".json"
        return s3_key

    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        s3_key = self._get_json_s3_key(key)
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            content = response['Body'].read().decode('utf-8')
            return json.loads(content)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.debug(f"S3 JSON object {s3_key} not found in {self.bucket_name} for key '{key}'")
                return None
            logger.error(f"Error getting S3 JSON object {s3_key} from {self.bucket_name} for key '{key}': {e}", exc_info=True)
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from S3 object {s3_key} for key '{key}': {e}", exc_info=True)
            raise # Or return None / custom exception

    def put_json(self, key: str, value: Dict[str, Any]) -> None:
        s3_key = self._get_json_s3_key(key)
        try:
            json_string = json.dumps(value, indent=4, ensure_ascii=False)
            self.s3_client.put_object(
                Bucket=self.bucket_name, 
                Key=s3_key, 
                Body=json_string.encode('utf-8'),
                ContentType='application/json'
            )
            logger.debug(f"Successfully put S3 JSON object {s3_key} to {self.bucket_name} for key '{key}'")
        except ClientError as e:
            logger.error(f"Error putting S3 JSON object {s3_key} to {self.bucket_name} for key '{key}': {e}", exc_info=True)
            raise
        except IOError as e: 
            logger.error(f"IOError before S3 JSON put for key {s3_key}: {e}", exc_info=True)
            raise

    def delete_json(self, key: str) -> None:
        s3_key = self._get_json_s3_key(key)
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.debug(f"Successfully deleted S3 JSON object {s3_key} from {self.bucket_name} for key '{key}'")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.debug(f"Attempted to delete non-existent S3 JSON object {s3_key}. No action.")
            else:
                logger.warning(f"Error deleting S3 JSON object {s3_key}: {e}", exc_info=True)
                raise

    # --- Binary Methods --- 
    def _get_binary_s3_key(self, key: str) -> str:
        # For binary files, use the key as is, removing leading slash.
        return key.lstrip('/')

    def get_binary(self, key: str) -> Optional[bytes]:
        s3_key = self._get_binary_s3_key(key)
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response['Body'].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.debug(f"S3 binary object {s3_key} not found in {self.bucket_name} for key '{key}'")
                return None
            logger.error(f"Error getting S3 binary object {s3_key} from {self.bucket_name} for key '{key}': {e}", exc_info=True)
            raise

    def put_binary(self, key: str, value: bytes, content_type: Optional[str] = None) -> None:
        s3_key = self._get_binary_s3_key(key)
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name, 
                Key=s3_key, 
                Body=value,
                **extra_args
            )
            logger.debug(f"Successfully put S3 binary object {s3_key} to {self.bucket_name} for key '{key}' with content_type: {content_type}")
        except ClientError as e:
            logger.error(f"Error putting S3 binary object {s3_key} to {self.bucket_name} for key '{key}': {e}", exc_info=True)
            raise

    def delete_binary(self, key: str) -> None:
        s3_key = self._get_binary_s3_key(key)
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.debug(f"Successfully deleted S3 binary object {s3_key} from {self.bucket_name} for key '{key}'")
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.debug(f"Attempted to delete non-existent S3 binary object {s3_key}. No action.")
            else:
                logger.warning(f"Error deleting S3 binary object {s3_key}: {e}", exc_info=True)
                raise
