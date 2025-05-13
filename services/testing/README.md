# Herramientas de Testing para TauseStack

Este módulo proporciona herramientas y utilidades para facilitar las pruebas de aplicaciones construidas con TauseStack, permitiendo probar con datos reales pero en entornos controlados.

## Características principales

- **Testing con datos reales**: Pruebas reales contra Supabase sin simular los datos
- **Limpieza automática**: Eliminación de datos de prueba después de cada ejecución
- **Fixtures preparados**: Para pytest y otros frameworks de testing
- **Generadores de datos**: Fácil creación de datos para pruebas

## Componentes

### 1. Helpers para Supabase

Permite realizar pruebas contra una instancia real de Supabase, garantizando que los datos de prueba se limpien correctamente.

```python
from services.testing.helpers.supabase_test_helpers import supabase_fixture, with_test_user

# Configurar fixtures
supabase = supabase_fixture()
test_user = with_test_user()

async def test_operacion_con_supabase(supabase, test_user):
    # Crear datos de prueba
    resultado = await supabase.create_test_data(MiModelo, {
        "campo": "valor",
        "usuario_id": test_user["user_id"]
    })
    
    assert resultado.id is not None
    # Las pruebas se ejecutan y los datos se limpian automáticamente
```

### 2. Helpers para Autenticación 

Facilita probar componentes que requieren autenticación, permisos o roles.

```python
from services.testing.helpers.auth_test_helpers import test_auth_provider, test_user, test_admin

async def test_validacion_permisos(test_auth_provider, test_admin):
    # Probar que un admin tiene los permisos correctos
    identity = test_admin["identity"]
    has_permission = await test_auth_provider.validate_permission(
        identity, "admin:all"
    )
    assert has_permission is True
```

### 3. Helpers para Base de Datos

Proporciona utilidades para pruebas de operaciones CRUD y consultas.

```python
from services.testing.helpers.database_test_helpers import db_context, test_data_factory

async def test_consulta_datos(db_context, test_data_factory):
    # Crear datos estructurados para pruebas
    usuario = await test_data_factory.create_user_profile()
    nota1 = await test_data_factory.create_note(usuario_id=usuario["user_id"])
    nota2 = await test_data_factory.create_note(usuario_id=usuario["user_id"])
    
    # Ejecutar consulta
    from services.database.interfaces.db_adapter import FilterCondition
    resultado = await db_context.db_adapter.query(
        Nota,
        conditions=[FilterCondition.equals("usuario_id", usuario["user_id"])]
    )
    
    assert len(resultado.data) == 2
    # Los datos se eliminan automáticamente al finalizar
```

## Configuración

### Para Supabase

1. Configura las variables de entorno:
   ```bash
   SUPABASE_TEST_URL=https://tu-proyecto-test.supabase.co
   SUPABASE_TEST_KEY=tu-api-key-de-test
   CLEANUP_TESTS=true
   ```

2. O personaliza la configuración programáticamente:
   ```python
   from services.testing.helpers.supabase_test_helpers import SupabaseTestConfig, SupabaseTestClient
   
   config = SupabaseTestConfig(
       supabase_url="https://tu-proyecto-test.supabase.co",
       supabase_key="tu-api-key-de-test",
       cleanup_after_tests=True
   )
   
   client = SupabaseTestClient(config)
   ```

## Mejores prácticas

1. **Usar instancias separadas**: Para pruebas, utiliza una instancia de Supabase diferente a la de producción.
2. **Limpieza automática**: Aprovecha la limpieza automática de datos para evitar acumulación de datos de prueba.
3. **Aislar pruebas**: Cada prueba debe crear sus propios datos y no depender de otras pruebas.
4. **Evitar efectos secundarios**: Asegúrate de que las pruebas no tengan efectos en el entorno real.

## Ejemplos completos

Consulta la carpeta `examples/testing/` para ver ejemplos completos de cómo implementar pruebas para tu aplicación TauseStack.

```python
# Ejemplo de test completo
import pytest
from services.testing.helpers.supabase_test_helpers import supabase_fixture
from services.testing.helpers.auth_test_helpers import test_user

# Setup fixtures
supabase = supabase_fixture()
user = test_user()

@pytest.mark.asyncio
async def test_crear_y_consultar(supabase, user):
    # 1. Crear datos
    nota = await supabase.create_test_data(Nota, {
        "titulo": "Mi nota de prueba",
        "contenido": "Contenido de prueba",
        "usuario_id": user["id"]
    })
    
    # 2. Verificar creación
    assert nota.id is not None
    assert nota.titulo == "Mi nota de prueba"
    
    # 3. Consultar datos
    from services.database.interfaces.db_adapter import FilterCondition
    resultado = await supabase.db_adapter.query(
        Nota,
        conditions=[FilterCondition.equals("id", nota.id)]
    )
    
    # 4. Verificar resultados
    assert len(resultado.data) == 1
    assert resultado.data[0].titulo == "Mi nota de prueba"
```
