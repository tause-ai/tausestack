# Manual Técnico de TauseStack

## Introducción

TauseStack es un framework modular para el desarrollo rápido de aplicaciones, diseñado para proporcionar abstracciones y herramientas que simplifican la creación de sistemas complejos. Este manual técnico proporciona una visión detallada de todos los componentes del framework y cómo utilizarlos en conjunto.

## Índice

1. [Arquitectura del Framework](#arquitectura-del-framework)
2. [Sistema de Autenticación](#sistema-de-autenticación)
3. [Adaptadores de Base de Datos](#adaptadores-de-base-de-datos)
4. [Integraciones con Frameworks Web](#integraciones-con-frameworks-web)
5. [Generador de Migraciones](#generador-de-migraciones)
6. [Herramientas de Testing](#herramientas-de-testing)
7. [CLI y Scaffolding](#cli-y-scaffolding)
8. [Integración de Componentes](#integración-de-componentes)

---

## Arquitectura del Framework

TauseStack utiliza un diseño modular basado en interfaces abstractas y adaptadores concretos. Esta arquitectura permite desacoplar componentes y facilita la extensibilidad.

### Principios de Diseño

1. **Interfaces Abstractas**: Definen contratos que todos los implementadores deben seguir
2. **Adaptadores Concretos**: Implementan las interfaces para tecnologías específicas
3. **Inyección de Dependencias**: Los componentes reciben sus dependencias en vez de crearlas
4. **Configuración Centralizada**: Parámetros y opciones unificados

### Estructura de Directorios

```
tausestack/
├── cli/                    # Herramientas de línea de comandos
├── docs/                   # Documentación técnica
├── examples/               # Ejemplos de uso
├── services/               # Componentes principales
│   ├── auth/               # Sistema de autenticación
│   ├── database/           # Adaptadores de base de datos
│   ├── integrations/       # Integraciones con frameworks
│   ├── mcp_client/         # Cliente MCP
│   └── testing/            # Herramientas de testing
└── templates/              # Plantillas para CLI
```

## Sistema de Autenticación

El sistema de autenticación está diseñado para ser flexible y compatible con múltiples proveedores.

### Interfaces Principales

- `AuthProvider`: Define el contrato para todos los proveedores de autenticación
- `UserIdentity`: Modelo que representa la identidad de un usuario autenticado
- `Permission` y `Role`: Representan permisos y roles para autorización

### Adaptadores Implementados

- **JWTAuthProvider**: Implementación base con JWT
- **SupabaseAuthProvider**: Integración con Supabase Auth

### Ejemplo de Uso

```python
from services.auth.adapters.supabase_provider import SupabaseAuthProvider

# Inicializar proveedor
auth_provider = SupabaseAuthProvider()
await auth_provider.initialize({
    "supabase_url": "https://tu-proyecto.supabase.co",
    "supabase_key": "tu-api-key"
})

# Autenticar usuario
identity = await auth_provider.authenticate({
    "auth_type": "password",
    "email": "usuario@ejemplo.com",
    "password": "contraseña"
})

# Verificar permisos
has_permission = await auth_provider.validate_permission(
    identity, "read:datos"
)
```

## Adaptadores de Base de Datos

El sistema de base de datos proporciona una interfaz unificada para operaciones CRUD y consultas avanzadas.

### Interfaces Principales

- `DatabaseAdapter`: Contrato para todos los adaptadores de bases de datos
- `FilterCondition`: Define condiciones para consultas
- `QueryOptions`: Opciones para paginación, ordenamiento, etc.

### Adaptadores Implementados

- **SupabaseDatabaseAdapter**: Integración con PostgreSQL a través de Supabase

### Ejemplo de Uso

```python
from services.database.adapters.supabase.client import SupabaseDatabaseAdapter
from services.database.interfaces.db_adapter import FilterCondition, QueryOptions
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
    "supabase_key": "tu-api-key"
})

# Crear registro
usuario = await db.create(Usuario, {
    "nombre": "Ejemplo",
    "email": "ejemplo@mail.com"
})

# Consultar con filtros
resultado = await db.query(
    Usuario,
    conditions=[FilterCondition.contains("email", "mail.com")],
    options=QueryOptions(limit=5)
)
```

## Integraciones con Frameworks Web

TauseStack proporciona integraciones con frameworks web populares para facilitar el desarrollo.

### Integraciones Implementadas

- **FastAPI**: Integración completa con FastAPI para crear APIs REST

### Ejemplo con FastAPI

```python
from fastapi import FastAPI
from services.integrations.fastapi.supabase_fastapi import SupabaseFastAPI

# Crear aplicación
app = FastAPI()

# Inicializar integración
supabase = SupabaseFastAPI(app)

# Usar dependencias para autenticación y base de datos
@app.get("/datos-protegidos")
async def datos_protegidos(
    current_user = Depends(supabase.get_current_user),
    db = Depends(supabase.get_db_adapter)
):
    return {"mensaje": f"Hola, {current_user.email}"}

# Generar routers CRUD automáticamente
productos_router = supabase.crud_router_factory(
    model=Producto,
    prefix="/productos"
)
app.include_router(productos_router)
```

## Generador de Migraciones

El generador de migraciones permite convertir modelos Pydantic en esquemas SQL para Supabase.

### Componentes Principales

- `MigrationGenerator`: Genera scripts SQL a partir de modelos
- `TableDefinition`: Define una tabla SQL con columnas, índices, etc.
- `RLSPolicy`: Define políticas de Row Level Security para Supabase

### Ejemplo de Uso

```python
from services.database.migrations.generator import MigrationGenerator
from pydantic import BaseModel, Field

# Definir modelos
class Producto(BaseModel):
    id: str
    nombre: str = Field(..., description="Nombre del producto")
    precio: float
    usuario_id: str

# Generar migración SQL
sql = MigrationGenerator.generate_migration([Producto])
print(sql)
```

### Usando el CLI

```bash
python -m services.database.migrations.cli ruta/a/modelos.py --output migracion.sql
```

## Herramientas de Testing

TauseStack incluye herramientas específicas para facilitar el testing de aplicaciones.

### Componentes Principales

- `supabase_test_helpers`: Para probar integraciones con Supabase
- `auth_test_helpers`: Para probar sistemas de autenticación
- `database_test_helpers`: Para probar operaciones de base de datos

### Ejemplo de Prueba

```python
import pytest
from services.testing.helpers.supabase_test_helpers import supabase_fixture, with_test_user

# Configurar fixtures
supabase = supabase_fixture()
test_user = with_test_user()

@pytest.mark.asyncio
async def test_crear_dato(supabase, test_user):
    # Crear datos de prueba
    resultado = await supabase.create_test_data(MiModelo, {
        "campo": "valor",
        "usuario_id": test_user["user_id"]
    })
    
    assert resultado.id is not None
    # Las pruebas se ejecutan y los datos se limpian automáticamente
```

## CLI y Scaffolding

TauseStack proporciona herramientas de línea de comandos para iniciar proyectos rápidamente.

### Comandos Principales

- `init`: Crea un nuevo proyecto basado en templates
- `dev`: Inicia el entorno de desarrollo
- `test`: Ejecuta pruebas del proyecto
- `format` y `lint`: Herramientas para código limpio

### Tipos de Proyectos Soportados

- **fastapi-supabase**: API con FastAPI y Supabase
- **website**: Sitio web estático
- **crm**: Sistema CRM básico
- **ecommerce**: Tienda en línea
- **chatbot**: Bot conversacional
- **agent**: Agente inteligente

### Ejemplo de Uso

```bash
# Crear nuevo proyecto
tause init mi-api --type fastapi-supabase

# Iniciar entorno de desarrollo
cd mi-api
tause dev

# Ejecutar pruebas
tause test
```

## Integración de Componentes

Esta sección muestra cómo integrar múltiples componentes de TauseStack para crear aplicaciones completas.

### Aplicación Completa con FastAPI y Supabase

```python
# Importaciones
from fastapi import FastAPI, Depends
from pydantic import BaseModel
import os

# Componentes de TauseStack
from services.integrations.fastapi.supabase_fastapi import SupabaseFastAPI
from services.auth.interfaces.auth_provider import UserIdentity
from services.database.interfaces.db_adapter import FilterCondition

# Modelos
class Item(BaseModel):
    id: str = None
    name: str
    owner_id: str = None

# App FastAPI
app = FastAPI()

# Configuración e inicialización
config = {
    "supabase_url": os.getenv("SUPABASE_URL"),
    "supabase_key": os.getenv("SUPABASE_KEY")
}
supabase = SupabaseFastAPI(app)

# Endpoints con autenticación
@app.get("/items/me")
async def get_my_items(
    user: UserIdentity = Depends(supabase.get_current_user),
    db = Depends(supabase.get_db_adapter)
):
    result = await db.query(
        Item,
        conditions=[FilterCondition.equals("owner_id", user.id)]
    )
    return result.data

# Router CRUD autogenerado
items_router = supabase.crud_router_factory(
    model=Item,
    prefix="/items"
)
app.include_router(items_router)
```

## Resumen

TauseStack proporciona un conjunto completo de herramientas y abstracciones para desarrollar aplicaciones modernas de forma rápida y con buenas prácticas. La arquitectura modular permite adoptar solo los componentes necesarios para cada proyecto y extender el framework según las necesidades específicas.

Para un tutorial paso a paso o ejemplos adicionales, consulta la carpeta `/examples` del repositorio.

---

© TauseStack Framework - 2025
