# Módulo de almacenamiento (`services/storage`)

Este módulo provee interfaces y adaptadores para gestionar archivos en distintos backends, siguiendo la arquitectura desacoplada de TauseStack.

## Proveedores disponibles
- `LocalStorageProvider`: almacenamiento local, útil para desarrollo y pruebas.
- `SupabaseStorageProvider`: integración con Supabase Storage (requiere `supabase-py`).

## Ejemplo de uso
```python
from services.storage import SupabaseStorageProvider
provider = SupabaseStorageProvider()
provider.save("folder/ejemplo.txt", b"contenido de prueba")
data = provider.load("folder/ejemplo.txt")
print(data)
```

## Estrategia de testing
- Los tests se encuentran en `tests/test_supabase_storage_provider.py`.
- Requieren variables de entorno:
  - `SUPABASE_URL`, `SUPABASE_KEY` (y opcional `SUPABASE_BUCKET`)
- Se omiten automáticamente si falta configuración.
- Cubren: guardar, leer, listar y borrar archivos.

## Buenas prácticas
- Siempre usa la interfaz `StorageProvider` para desacoplar la lógica de negocio.
- Prefiere `SupabaseStorageProvider` en producción; `LocalStorageProvider` para desarrollo.
- Maneja errores de red y permisos.
- Nunca subas datos sensibles a buckets públicos sin cifrado.

## Extensión y próximos pasos
- Agregar serializadores/deserializadores para JSON, texto, binario, DataFrames, etc.
- Implementar tests para casos de error y archivos grandes.
- Documentar integración con otros backends si se agregan.

---

> Última actualización: 2025-05-14
