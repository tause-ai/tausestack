# Interfaces de Pasarelas de Pago

Este directorio contiene las interfaces abstractas para la integración de pasarelas de pago en aplicaciones Tausestack.

## Interfaces Principales

### PaymentGateway

La interfaz `PaymentGateway` define el contrato que deben implementar todos los adaptadores de pasarelas de pago, independientemente del proveedor específico (Wompi, ePayco, PayU, etc.).

```python
from services.payments.interfaces.payment_gateway import PaymentGateway

class MiPasarelaPago(PaymentGateway):
    # Implementar métodos abstractos aquí
```

Métodos principales:
- `initialize`: Inicializa la pasarela con configuración (API keys, modo)
- `create_transaction`: Crea una nueva transacción de pago
- `get_transaction_status`: Consulta el estado actual de una transacción
- `process_webhook`: Procesa notificaciones de la pasarela (webhooks)
- `get_checkout_url`: Genera URL para checkout o redirección

### PaymentTransaction

Modelo de datos estandarizado para representar una transacción de pago, independiente del proveedor:

```python
from services.payments.interfaces.payment_gateway import PaymentTransaction, TransactionStatus

# Crear una transacción
tx = PaymentTransaction(
    id="tx_123",
    amount=25000,
    currency="COP",
    reference="orden-123",
    status=TransactionStatus.PENDING
)
```

## TransactionStatus

Enum que estandariza los estados de transacción entre diferentes pasarelas:

```python
from services.payments.interfaces.payment_gateway import TransactionStatus

# Ejemplos de uso
if transaction.status == TransactionStatus.SUCCESS:
    # Procesar transacción exitosa
elif transaction.status == TransactionStatus.FAILED:
    # Manejar fallo
```

## Recomendaciones de Implementación

1. **Mapeo de estados**: Convierte los estados específicos del proveedor a TransactionStatus
2. **Manejo de errores**: Captura y traduce errores específicos del proveedor
3. **Seguridad**: Valida firmas en webhooks cuando el proveedor lo soporte
4. **Idempotencia**: Implementa mecanismos para evitar procesamiento duplicado
5. **Configuración segura**: Utiliza la gestión de secrets de Tausestack para credenciales

## Ejemplos de Adaptadores

Consulta `/services/payments/adapters/` para ver ejemplos de implementaciones concretas para proveedores específicos.
