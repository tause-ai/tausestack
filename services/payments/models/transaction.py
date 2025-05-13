# Este archivo está obsoleto. Se mantiene temporalmente por compatibilidad.
# Usar interfaces.payment_gateway.PaymentTransaction en su lugar.

from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class PaymentTransaction(BaseModel):
    """
    Modelo de transacción de pago específico para Wompi.
    DEPRECATED: Usar interfaces.payment_gateway.PaymentTransaction
    """
    id: str  # UUID interno
    user_id: str
    module_id: str
    wompi_transaction_id: Optional[str]
    status: str  # pending, success, failed, cancelled
    amount: int
    currency: str
    created_at: datetime
    updated_at: datetime
    raw_response: Optional[Dict] = None
