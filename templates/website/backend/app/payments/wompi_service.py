import requests
from typing import Dict, Any, Optional

class WompiService:
    """Servicio para integración con la pasarela de pagos Wompi (Colombia)."""
    BASE_URL = "https://production.wompi.co/v1"

    def __init__(self, public_key: str, private_key: str):
        self.public_key = public_key
        self.private_key = private_key

    def create_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea una transacción en Wompi.
        Args:
            data: Diccionario con los datos de la transacción.
        Returns:
            Respuesta de la API de Wompi.
        Raises:
            Exception en caso de error.
        """
        url = f"{self.BASE_URL}/transactions"
        headers = {"Authorization": f"Bearer {self.private_key}", "Content-Type": "application/json"}
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Consulta el estado de una transacción.
        Args:
            transaction_id: ID de la transacción en Wompi.
        Returns:
            Respuesta de la API de Wompi.
        """
        url = f"{self.BASE_URL}/transactions/{transaction_id}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def validate_signature(self, data: str, signature: str) -> bool:
        """Valida la firma de Wompi para callbacks/webhooks.
        Args:
            data: Cadena de datos recibida.
            signature: Firma recibida.
        Returns:
            True si la firma es válida, False en caso contrario.
        """
        # Implementación básica, para producción usar HMAC SHA256
        import hmac, hashlib
        expected = hmac.new(self.private_key.encode(), data.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
