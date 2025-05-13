# Integración FastAPI con Supabase

Este módulo proporciona una integración completa entre FastAPI y Supabase, simplificando enormemente el desarrollo de APIs con autenticación y operaciones en base de datos.

## Características principales

- **Inicialización automática** de clientes Supabase
- **Middleware integrado** para acceso a proveedores
- **Dependencias preparadas** para autenticación y base de datos
- **Generador de routers CRUD** para cualquier modelo Pydantic
- **Manejo automático de permisos** basado en propiedad de recursos

## Instalación

El módulo está incluido en el framework TauseStack. No se requiere instalación adicional si ya tienes el framework.

## Uso básico

### 1. Inicializar la integración

```python
from fastapi import FastAPI
from services.integrations.fastapi.supabase_fastapi import SupabaseFastAPI

app = FastAPI()
supabase = SupabaseFastAPI(app)
```

### 2. Usar dependencias para autenticación

```python
@app.get("/ruta-protegida")
async def ruta_protegida(
    current_user = Depends(supabase.get_current_user)
):
    return {"mensaje": f"Hola, {current_user.email}"}
```

### 3. Acceder al adaptador de base de datos

```python
@app.get("/datos")
async def obtener_datos(
    current_user = Depends(supabase.get_current_user),
    db = Depends(supabase.get_db_adapter)
):
    resultados = await db.query(MiModelo, conditions=[...])
    return resultados.data
```

### 4. Generar routers CRUD automáticamente

```python
class Producto(BaseModel):
    id: Optional[UUID] = None
    nombre: str
    precio: float
    usuario_id: UUID

# Crear y registrar router CRUD automáticamente
productos_router = supabase.crud_router_factory(
    model=Producto,
    prefix="/productos",
    tags=["Productos"]
)

app.include_router(productos_router)
```

## API Generada Automáticamente

Para cada modelo, el `crud_router_factory` genera estos endpoints:

- `POST /prefix/` - Crear nuevo recurso
- `GET /prefix/` - Listar recursos (con paginación)
- `GET /prefix/{id}` - Obtener un recurso específico
- `PUT /prefix/{id}` - Actualizar un recurso
- `DELETE /prefix/{id}` - Eliminar un recurso

Todos los endpoints están protegidos con autenticación y verifican la propiedad del recurso cuando el modelo tiene `usuario_id` o `user_id`.

## Configuración avanzada

### Personalizar la configuración de Supabase

```python
from services.integrations.fastapi.supabase_fastapi import SupabaseConfig

config = SupabaseConfig(
    supabase_url="https://tu-proyecto.supabase.co",
    supabase_key="tu-api-key",
    debug_mode=True
)

supabase = SupabaseFastAPI(app, config=config)
```

### Usar proveedores personalizados

```python
supabase = SupabaseFastAPI(
    app,
    auth_provider_class=MiProveedorPersonalizado,
    db_adapter_class=MiAdaptadorPersonalizado
)
```

## Ejemplo completo

Consulta el ejemplo en `examples/integrations/fastapi_supabase_app.py` para ver una aplicación completa con autenticación, perfiles de usuario y notas personales.
