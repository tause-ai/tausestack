from pydantic import BaseModel
from typing import Literal
from datetime import datetime

class PaymentGatewayConfig(BaseModel):
    id: str
    company_id: str
    gateway: Literal["wompi", "epayco", "placetopay", "payu", "mercadopago"]
    public_key: str
    private_key: str
    active: bool = True
    created_at: datetime
    updated_at: datetime
