from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime

class TransactionStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class PaymentTransaction:
    """Estructura base para una transacción de pago."""
    
    def __init__(
        self,
        id: str,
        amount: int,
        currency: str,
        reference: str,
        status: TransactionStatus = TransactionStatus.PENDING,
        provider_transaction_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.amount = amount
        self.currency = currency
        self.reference = reference
        self.status = status
        self.provider_transaction_id = provider_transaction_id
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

class PaymentGateway(ABC):
    """
    Interfaz abstracta para pasarelas de pago.
    
    Esta clase define el contrato que todos los adaptadores de pasarela de pago deben implementar,
    independientemente del proveedor específico (Wompi, ePayco, MercadoPago, etc).
    """
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Inicializa la pasarela de pago con la configuración proporcionada.
        
        Args:
            config (Dict[str, Any]): Configuración específica del proveedor (API keys, etc).
            
        Returns:
            bool: True si la inicialización fue exitosa, False en caso contrario.
        """
        pass
    
    @abstractmethod
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
        """
        Crea una nueva transacción de pago.
        
        Args:
            amount (int): Monto en centavos/céntimos.
            currency (str): Código de moneda (ej: "COP", "USD").
            reference (str): Referencia única para la transacción.
            description (Optional[str]): Descripción del pago.
            customer_email (Optional[str]): Email del cliente.
            redirect_url (Optional[str]): URL de retorno después del pago.
            metadata (Optional[Dict[str, Any]]): Datos adicionales para la transacción.
            
        Returns:
            PaymentTransaction: Objeto con los datos de la transacción creada.
        """
        pass
    
    @abstractmethod
    async def get_transaction_status(self, transaction_id: str) -> PaymentTransaction:
        """
        Consulta el estado de una transacción.
        
        Args:
            transaction_id (str): ID de la transacción a consultar.
            
        Returns:
            PaymentTransaction: Objeto con los datos actualizados de la transacción.
        """
        pass
    
    @abstractmethod
    async def process_webhook(self, payload: Dict[str, Any]) -> PaymentTransaction:
        """
        Procesa una notificación webhook de la pasarela de pago.
        
        Args:
            payload (Dict[str, Any]): Datos enviados por la pasarela en el webhook.
            
        Returns:
            PaymentTransaction: Objeto con los datos actualizados de la transacción.
        """
        pass
    
    @abstractmethod
    def get_checkout_url(self, transaction: PaymentTransaction) -> str:
        """
        Obtiene la URL de checkout para redirigir al usuario.
        
        Args:
            transaction (PaymentTransaction): Transacción para la cual generar URL.
            
        Returns:
            str: URL completa para el proceso de pago.
        """
        pass
