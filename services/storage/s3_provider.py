"""
S3StorageProvider: Proveedor de almacenamiento basado en Amazon S3 para Tausestack.

Requiere boto3 y credenciales AWS configuradas (variables de entorno o archivo de configuración).
Incluye validación de claves/nombres alineada a la convención global.
Soporta operaciones CRUD y chunking eficiente para archivos grandes.
"""
import os
import math
import re
import boto3
from typing import List
from .provider import StorageProvider

class S3StorageProvider(StorageProvider):
    _key_regex = re.compile(r'^[a-zA-Z0-9._\-/]+$')

    def __init__(self, bucket_name: str, region_name: str = None):
        self.bucket_name = bucket_name
        self.s3 = boto3.client('s3', region_name=region_name)

    def _validate_key(self, path: str):
        if not self._key_regex.match(path):
            raise ValueError(f"Clave/nombre de archivo inválido: '{path}'. Debe cumplir la convención regex ^[a-zA-Z0-9._\-/]+$")
        if os.path.isabs(path) or '..' in path:
            raise ValueError(f"No se permiten rutas absolutas ni '..' en claves: '{path}'")

    def save(self, path: str, data: bytes) -> None:
        self._validate_key(path)
        self.s3.put_object(Bucket=self.bucket_name, Key=path, Body=data)

    def load(self, path: str) -> bytes:
        self._validate_key(path)
        obj = self.s3.get_object(Bucket=self.bucket_name, Key=path)
        return obj['Body'].read()

    def list(self, prefix: str = "") -> List[str]:
        if prefix:
            self._validate_key(prefix)
        paginator = self.s3.get_paginator('list_objects_v2')
        result = []
        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
            for content in page.get('Contents', []):
                result.append(content['Key'])
        return result

    def delete(self, path: str) -> None:
        self._validate_key(path)
        self.s3.delete_object(Bucket=self.bucket_name, Key=path)

    def save_chunk(self, path: str, chunk: bytes, chunk_index: int) -> None:
        self._validate_key(path)
        chunk_key = f"{path}.chunk{chunk_index}"
        self.s3.put_object(Bucket=self.bucket_name, Key=chunk_key, Body=chunk)

    def load_chunk(self, path: str, chunk_index: int, chunk_size: int) -> bytes:
        self._validate_key(path)
        chunk_key = f"{path}.chunk{chunk_index}"
        obj = self.s3.get_object(Bucket=self.bucket_name, Key=chunk_key)
        return obj['Body'].read(chunk_size)

    def get_num_chunks(self, path: str, chunk_size: int) -> int:
        self._validate_key(path)
        obj = self.s3.head_object(Bucket=self.bucket_name, Key=path)
        file_size = obj['ContentLength']
        return math.ceil(file_size / chunk_size)
