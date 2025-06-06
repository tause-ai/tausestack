# Módulo de gestión de secretos (`services/secrets`)

Este módulo provee una interfaz unificada y desacoplada para acceder a secretos y variables sensibles en TauseStack.

## Proveedores disponibles
- `EnvSecretsProvider`: obtiene secretos desde variables de entorno.
- `SupabaseSecretsProvider`: obtiene secretos desde una tabla segura en Supabase (con fallback opcional al entorno).

## Ejemplo de uso
```python
from services.secrets import EnvSecretsProvider, SupabaseSecretsProvider

# Entorno
provider = EnvSecretsProvider()
valor = provider.get("API_KEY")

# Supabase
provider = SupabaseSecretsProvider()
valor = provider.get("API_KEY")
```

## Estrategia de testing
- Los tests están en `tests/test_secrets_provider.py`.
- Se cubren casos de entorno, Supabase y fallback.
- Los tests de Supabase requieren:
  - Variables `SUPABASE_URL`, `SUPABASE_KEY` y una tabla `secrets` con registros de prueba.

## Buenas prácticas y advertencias
- Nunca almacenes secretos productivos en código o repositorios.
- Prefiere `SupabaseSecretsProvider` para producción y `EnvSecretsProvider` para desarrollo/local.
- Usa fallback solo si es seguro para tu caso de uso.
- Revisa los permisos y el cifrado de la tabla `secrets` en Supabase.

## Extensión
- Puedes implementar nuevos proveedores (Vault, AWS Secrets Manager, etc) heredando de `SecretsProvider`.
- Considera agregar caché local o rotación de claves para mayor seguridad.

---

> Última actualización: 2025-05-14
