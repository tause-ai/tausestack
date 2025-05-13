# Framework de Pasarelas de Pago

Librería base para integrar y configurar diferentes pasarelas de pago en aplicaciones Tausestack. Este framework proporciona interfaces abstractas y utilidades para implementar adaptadores personalizados para distintas pasarelas (Wompi, ePayco, PayU, etc.).

## Estructura del Framework

- `interfaces/`: Contratos e interfaces abstractas para implementar adaptadores de pasarelas
- `adapters/`: Implementaciones concretas para pasarelas específicas (ejemplos)
- `models/`: Modelos de datos compartidos
- `api/`: Ejemplos de endpoints para integrar el framework en una API

## Interfaces Principales

### PaymentGateway

Interfaz base para implementar adaptadores de pasarelas de pago:

```python
from services.payments.interfaces.payment_gateway import PaymentGateway, PaymentTransaction

class MiPasarelaPersonalizada(PaymentGateway):
    async def initialize(self, config):
        # Inicializar con credenciales
        self.api_key = config.get("api_key")
        return True
        
    async def create_transaction(self, amount, currency, reference, ...):
        # Implementación específica para crear transacción
        ...
        
    async def get_transaction_status(self, transaction_id):
        # Obtener estado actualizado
        ...
```

### PaymentTransaction

Modelo estándar para representar transacciones, independiente de la pasarela:

```python
from services.payments.interfaces.payment_gateway import PaymentTransaction, TransactionStatus

# Crear una transacción
transaction = PaymentTransaction(
    id="tx_123",
    amount=15000,
    currency="COP",
    reference="mi-referencia-unica",
    status=TransactionStatus.PENDING
)
```

## Cómo Implementar una Nueva Pasarela

1. Crea una subclase de `PaymentGateway`
2. Implementa todos los métodos abstractos
3. Mapea los estados y campos propios de la pasarela a la estructura estándar del framework

## Ejemplos Incluidos

El framework incluye el adaptador para Wompi como ejemplo:

```python
from services.payments.adapters.wompi.client import WompiGateway

# Inicializar
gateway = WompiGateway()
await gateway.initialize({
    "public_key": "tu_llave_publica",
    "private_key": "tu_llave_privada",
    "test_mode": True
})

# Crear transacción
transaction = await gateway.create_transaction(
    amount=15000,
    currency="COP",
    reference="pedido-123",
    customer_email="cliente@ejemplo.com"
)

# Obtener URL de checkout
checkout_url = gateway.get_checkout_url(transaction)
```
