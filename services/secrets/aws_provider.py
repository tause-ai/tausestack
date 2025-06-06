"""
AWSSecretsManagerProvider: Proveedor de secretos basado en AWS Secrets Manager para Tausestack.

Requiere boto3 y configuración de credenciales AWS.
Incluye patrón seguro y desacoplado, alineado a la convención global.
"""
import os
from typing import Optional
import boto3
from .provider import SecretsProvider

class AWSSecretsManagerProvider(SecretsProvider):
    def __init__(self, region_name: str = None):
        self.region_name = region_name or os.getenv("AWS_REGION") or "us-east-1"
        self.client = boto3.client("secretsmanager", region_name=self.region_name)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        try:
            response = self.client.get_secret_value(SecretId=key)
            if "SecretString" in response:
                return response["SecretString"]
            elif "SecretBinary" in response:
                return response["SecretBinary"].decode()
        except Exception:
            return default
