# Generador de Migraciones para Supabase

Este módulo permite generar automáticamente scripts SQL para Supabase a partir de modelos Pydantic, facilitando enormemente la creación y mantenimiento de esquemas de base de datos.

## Características principales

- **Generación automática de tablas** a partir de modelos Pydantic
- **Definición de relaciones** basada en convenciones de nombres
- **Políticas RLS** (Row Level Security) preconfiguradas
- **Índices optimizados** generados automáticamente
- **Soporte para timestamps** (created_at, updated_at)
- **CLI integrado** para facilitar su uso

## Uso básico

### 1. Definir modelos

Crea tus modelos Pydantic con anotaciones:

```python
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional

class Producto(BaseModel):
    id: Optional[UUID] = Field(None)
    nombre: str = Field(..., description="Nombre del producto")
    precio: float = Field(..., description="Precio en pesos")
    usuario_id: UUID = Field(..., description="ID del creador")
    publicado: bool = Field(False)
```

### 2. Generar migración

Utiliza el CLI para generar el SQL:

```bash
python -m services.database.migrations.cli ruta/a/tus/modelos.py --output migracion.sql
```

### 3. Ejecutar en Supabase

Ejecuta el script resultante en el SQL Editor de Supabase.

## Características avanzadas

### Personalización de tablas

Configura el nombre de la tabla:

```python
class Usuario(BaseModel):
    # ...campos...
    
    # Nombre explícito de tabla
    __tablename__ = "usuarios"
```

### Políticas RLS personalizadas

Agrega políticas de seguridad personalizadas:

```python
class Documento(BaseModel):
    # ...campos...
    
    class Config:
        rls_policies = [
            {
                "name": "Política personalizada",
                "operation": "SELECT",
                "using": "condicion_personalizada()"
            }
        ]
```

### Índices personalizados

Define índices para optimizar consultas:

```python
class Pedido(BaseModel):
    # ...campos...
    
    class Config:
        indices = [
            {"columns": ["usuario_id", "fecha"], "unique": False},
            {"columns": ["codigo_referencia"], "unique": True}
        ]
```

## Mejores prácticas

1. **Usa ID UUID** para todas las tablas principales
2. **Incluye `user_id`** para aprovechar la generación automática de RLS
3. **Agrega descripciones** a los campos usando el parámetro `description`
4. **Define relaciones** usando el sufijo `_id` en los nombres de campo
5. **Revisa el SQL generado** antes de ejecutarlo en producción

## Ejemplo completo

Consulta el ejemplo en `/examples/database/modelo_migracion.py` y el SQL generado en `/examples/database/migracion_ejemplo.sql`.

## CLI: Opciones adicionales

```bash
# Ver ayuda
python -m services.database.migrations.cli --help

# Generar script drop
python -m services.database.migrations.cli ruta/modelo.py --drop

# Sin funciones auxiliares
python -m services.database.migrations.cli ruta/modelo.py --no-helpers
```
