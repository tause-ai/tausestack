import httpx
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from ...interfaces.payment_gateway import PaymentGateway, PaymentTransaction, TransactionStatus

class WompiGateway(PaymentGateway):
    """
    Implementación de la interfaz PaymentGateway para la pasarela de pagos Wompi.
    
    Esta clase concreta demuestra cómo implementar un adaptador para Wompi
    siguiendo el patrón definido por la interfaz.
    """
    
    def __init__(self):
        self.public_key = None
        self.private_key = None
        self.is_test_mode = True
        self.base_url = "https://sandbox.wompi.co/v1"
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Inicializa el cliente Wompi con las credenciales proporcionadas."""
        self.public_key = config.get("public_key")
        self.private_key = config.get("private_key")
        self.is_test_mode = config.get("test_mode", True)
        
        if not self.public_key:
            return False
            
        # En modo producción, usar la URL de producción
        if not self.is_test_mode:
            self.base_url = "https://production.wompi.co/v1"
            
        return True
    
    async def create_transaction(
        self, 
        amount: int,
        currency: str,
        reference: str,
        description: Optional[str] = None,
        customer_email: Optional[str] = None,
        redirect_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentTransaction:
        """Crea una transacción de pago en Wompi."""
        if not self.public_key:
            raise ValueError("Gateway no inicializada. Llama a initialize() primero.")
        
        url = f"{self.base_url}/transactions"
        
        payload = {
            "amount_in_cents": amount,
            "currency": currency,
            "reference": reference,
            "public_key": self.public_key,
        }
        
        if description:
            payload["description"] = description
        
        if customer_email:
            payload["customer_email"] = customer_email
            
        if redirect_url:
            payload["redirect_url"] = redirect_url
            
        if metadata:
            payload["metadata"] = metadata
        
        try:
            # Realizar la petición a Wompi
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                # Extraer datos de la respuesta
                wompi_tx_id = data.get("data", {}).get("id")
                
                # Crear y retornar objeto de transacción
                transaction = PaymentTransaction(
                    id=reference,
                    amount=amount,
                    currency=currency,
                    reference=reference,
                    status=TransactionStatus.PENDING,
                    provider_transaction_id=wompi_tx_id,
                    metadata={"wompi_response": data, "custom_metadata": metadata or {}},
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                return transaction
        except Exception as e:
            # En caso de error, crear transacción con estado fallido
            return PaymentTransaction(
                id=reference,
                amount=amount,
                currency=currency,
                reference=reference,
                status=TransactionStatus.FAILED,
                metadata={"error": str(e), "custom_metadata": metadata or {}},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
    
    async def get_transaction_status(self, transaction_id: str) -> PaymentTransaction:
        """Consulta el estado de una transacción en Wompi."""
        if not self.private_key:
            raise ValueError("Se requiere private_key para consultar el estado de una transacción.")
        
        url = f"{self.base_url}/transactions/{transaction_id}"
        headers = {"Authorization": f"Bearer {self.private_key}"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                # Mapear estado de Wompi a nuestro enum
                wompi_status = data.get("data", {}).get("status")
                status_map = {
                    "PENDING": TransactionStatus.PENDING,
                    "APPROVED": TransactionStatus.SUCCESS,
                    "DECLINED": TransactionStatus.FAILED,
                    "VOIDED": TransactionStatus.CANCELLED,
                    "ERROR": TransactionStatus.FAILED,
                }
                mapped_status = status_map.get(wompi_status, TransactionStatus.PENDING)
                
                # Crear y retornar objeto de transacción actualizado
                return PaymentTransaction(
                    id=data.get("data", {}).get("reference"),
                    amount=data.get("data", {}).get("amount_in_cents"),
                    currency=data.get("data", {}).get("currency"),
                    reference=data.get("data", {}).get("reference"),
                    status=mapped_status,
                    provider_transaction_id=transaction_id,
                    metadata={"wompi_response": data},
                    created_at=datetime.utcnow(),  # Idealmente parse from response
                    updated_at=datetime.utcnow()
                )
        except Exception as e:
            # En caso de error, retornar transacción con datos mínimos
            return PaymentTransaction(
                id=transaction_id,
                amount=0,
                currency="",
                reference="",
                status=TransactionStatus.FAILED,
                provider_transaction_id=transaction_id,
                metadata={"error": str(e)},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
    
    async def process_webhook(self, payload: Dict[str, Any]) -> PaymentTransaction:
        """Procesa una notificación webhook de Wompi."""
        # En producción, validar la firma con la llave privada
        
        # Extraer datos del webhook
        event_type = payload.get("event")
        transaction_data = payload.get("data", {}).get("transaction", {})
        reference = transaction_data.get("reference")
        status = transaction_data.get("status")
        amount = transaction_data.get("amount_in_cents")
        currency = transaction_data.get("currency")
        wompi_tx_id = transaction_data.get("id")
        
        # Mapear estado de Wompi a nuestro enum
        status_map = {
            "PENDING": TransactionStatus.PENDING,
            "APPROVED": TransactionStatus.SUCCESS,
            "DECLINED": TransactionStatus.FAILED,
            "VOIDED": TransactionStatus.CANCELLED,
            "ERROR": TransactionStatus.FAILED,
        }
        mapped_status = status_map.get(status, TransactionStatus.PENDING)
        
        # Crear y retornar objeto de transacción actualizado
        return PaymentTransaction(
            id=reference,
            amount=amount,
            currency=currency,
            reference=reference,
            status=mapped_status,
            provider_transaction_id=wompi_tx_id,
            metadata={"wompi_webhook": payload},
            updated_at=datetime.utcnow()
        )
    
    def get_checkout_url(self, transaction: PaymentTransaction) -> str:
        """Obtiene la URL de checkout de Wompi para redirigir al usuario."""
        if not self.public_key:
            raise ValueError("Gateway no inicializada. Llama a initialize() primero.")
        
        # Para Wompi, podemos construir la URL de checkout directamente
        base = "https://checkout.wompi.co/p/" if not self.is_test_mode else "https://sandbox.wompi.co/p/"
        
        return f"{base}?public-key={self.public_key}&reference={transaction.reference}&amount-in-cents={transaction.amount}&currency={transaction.currency}"
