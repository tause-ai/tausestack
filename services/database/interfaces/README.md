# Interfaces de Base de Datos

Este directorio contiene las interfaces abstractas para implementar adaptadores de bases de datos en aplicaciones Tausestack.

## Interfaces Principales

### DatabaseAdapter

La interfaz `DatabaseAdapter` define el contrato que deben implementar todos los adaptadores de bases de datos, independientemente de la tecnología específica (PostgreSQL, MySQL, etc.).

```python
from services.database.interfaces.db_adapter import DatabaseAdapter
from pydantic import BaseModel

class MiAdaptadorBD(DatabaseAdapter):
    # Implementar métodos abstractos aquí
```

Métodos principales:
- `initialize`: Inicializa el adaptador con configuración
- `create`: Crea un nuevo registro en la base de datos
- `read`: Lee un registro por su ID
- `update`: Actualiza un registro existente
- `delete`: Elimina un registro
- `query`: Consulta registros con filtros y opciones
- `execute_raw`: Ejecuta consultas nativas

### Modelos para filtros y consultas

El framework proporciona modelos estándar para consultas y filtros:

```python
from services.database.interfaces.db_adapter import FilterCondition, QueryOptions

# Crear filtros
filtros = [
    FilterCondition.equals("campo", "valor"),
    FilterCondition.greater_than("numero", 100),
    FilterCondition.contains("texto", "búsqueda")
]

# Opciones de consulta
opciones = QueryOptions(
    limit=10,
    offset=0,
    order_by="campo",
    order_direction="desc",
    include_count=True
)
```

## Adaptadores Implementados

### Supabase

Adaptador para PostgreSQL mediante Supabase:

```python
from services.database.adapters.supabase.client import SupabaseDatabaseAdapter
from pydantic import BaseModel

# Definir modelo
class Usuario(BaseModel):
    id: str
    nombre: str
    email: str
    
# Inicializar adaptador
db = SupabaseDatabaseAdapter()
await db.initialize({
    "supabase_url": "https://tu-proyecto.supabase.co",
    "supabase_key": "tu-api-key-publica-de-supabase"
})

# Crear registro
usuario = await db.create(Usuario, {
    "nombre": "Ejemplo",
    "email": "ejemplo@mail.com"
})

# Consultar registros
resultado = await db.query(
    Usuario,
    conditions=[FilterCondition.contains("email", "mail.com")],
    options=QueryOptions(limit=5)
)

# Iterar resultados
for user in resultado.data:
    print(f"Usuario: {user.nombre}")
```

## Recomendaciones de Implementación

1. **Modelos**: Usa modelos Pydantic para definir la estructura de tus datos
2. **Transacciones**: Maneja operaciones complejas dentro de transacciones
3. **Condiciones**: Usa los constructores de FilterCondition para consultas seguras
4. **Seguridad**: Evita usar execute_raw con entrada no verificada

Consulta los ejemplos en `/examples/database/` para ver implementaciones completas.
