# Proveedores de Autenticación Tausestack

Este directorio contiene los adaptadores concretos para autenticación en Tausestack.

## Proveedor recomendado: SupabaseAuthProvider

`SupabaseAuthProvider` es el adaptador principal y recomendado para producción y desarrollo. Implementa la interfaz `AuthProvider` y aprovecha todas las capacidades de Supabase Auth (login, refresh, OAuth, multifactor, gestión de sesiones y claims).

### Ejemplo de uso
```python
from services.auth.adapters.supabase_provider import SupabaseAuthProvider

provider = SupabaseAuthProvider()
config = {
    "supabase_url": "https://<tu-proyecto>.supabase.co",
    "supabase_key": "<tu-api-key>",
    # Opcional: "jwt_secret": "<tu-jwt-secret>"
}
await provider.initialize(config)
```

## Proveedor alternativo: JWTAuthProvider (solo fallback)

`JWTAuthProvider` es un adaptador alternativo, útil solo para pruebas, desarrollo local o casos donde Supabase Auth no esté disponible. **No se recomienda su uso en producción.**

### Ejemplo de uso
```python
from services.auth.adapters.jwt_provider import JWTAuthProvider

provider = JWTAuthProvider()
config = {
    "secret_key": "clave-secreta-segura",
    # Opcional: "algorithm": "HS256", "access_token_expire_minutes": 30
}
await provider.initialize(config)
```

## Estrategia y cobertura de testing

Todos los adaptadores deben contar con tests unitarios y de integración que cubran los siguientes flujos críticos:
- Inicialización correcta y fallida.
- Autenticación por email/password y magic link.
- Validación de tokens.
- Refresh (renovación) de tokens.
- Revocación de tokens.

Los tests de `SupabaseAuthProvider` se encuentran en `tests/test_supabase_provider.py` y requieren variables de entorno reales:
- `SUPABASE_URL`, `SUPABASE_KEY` (proyecto de pruebas)
- `SUPABASE_TEST_EMAIL`, `SUPABASE_TEST_PASSWORD` (usuario de pruebas)

Los tests se omiten automáticamente si no hay entorno de pruebas configurado, evitando falsos negativos.

Puedes extender la cobertura agregando casos para OAuth, teléfono y manejo de errores.

---

## Buenas prácticas
- Siempre utiliza la interfaz `AuthProvider` para desacoplar tu lógica de negocio del proveedor concreto.
- Prefiere `SupabaseAuthProvider` para entornos reales.
- Usa `JWTAuthProvider` solo para pruebas o fallback controlado.
- Asegúrate de cubrir todos los flujos críticos con tests.
- Consulta la documentación de interfaces para extender o crear nuevos proveedores.

---

> Última actualización: 2025-05-14
