# SDK de Base de Datos TauseStack - Backend SQLAlchemy

El `SQLAlchemyBackend` proporciona una interfaz para interactuar con bases de datos relacionales utilizando SQLAlchemy de forma asíncrona. Permite realizar operaciones CRUD (Crear, Leer, Actualizar, Eliminar), gestionar transacciones de forma explícita o mediante un gestor de contexto, y ejecutar consultas SQL crudas para operaciones complejas o específicas de la base de datos.

## Uso Básico

Para utilizar `SQLAlchemyBackend`, necesitas definir tus modelos de datos Pydantic, tus modelos de tabla SQLAlchemy, y un mapeo entre ellos.

### 1. Definir Modelos Pydantic

Tus modelos Pydantic deben heredar de `tausestack.sdk.database.Model` (que es un alias de `pydantic.BaseModel` con configuración para `from_attributes=True` y un campo `id` opcional).

```python
# en tu_app/models_pydantic.py
from typing import Optional
from tausestack.sdk.database import Model, ItemID # ItemID es Union[int, str]

class UserPydantic(Model):
    id: Optional[ItemID] = None # Heredado de Model, pero puedes redefinirlo si es necesario
    username: str
    email: str
    is_active: bool = True

    # Config para Pydantic v2, ya incluido en sdk.database.Model
    # class Config:
    #     orm_mode = True # Pydantic v1
    #     from_attributes = True # Pydantic v2
```

### 2. Definir Modelos SQLAlchemy

Define tus tablas utilizando la base declarativa de SQLAlchemy.

```python
# en tu_app/models_sqla.py
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class UserSQLA(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
```

### 3. Crear el `model_mapping`

Este diccionario es esencial para que el backend sepa cómo convertir entre tus modelos Pydantic y SQLAlchemy.

```python
# en tu_app/database_setup.py
from .models_pydantic import UserPydantic
from .models_sqla import UserSQLA

model_mapping = {
    UserPydantic: UserSQLA,
    # ... otros mapeos de modelos ...
}
```

### 4. Inicializar `SQLAlchemyBackend`

Ahora puedes instanciar el backend.

```python
# en tu_app/database_setup.py
from sqlalchemy import MetaData
from tausestack.sdk.database import SQLAlchemyBackend
from .models_sqla import Base # La Base de tus modelos SQLAlchemy
# model_mapping definido arriba

DATABASE_URL = "sqlite+aiosqlite:///./test_app.db" # O tu URL de PostgreSQL, etc.

# La metadata de SQLAlchemy debe contener todas tus tablas
# Si usas la Base de declarative_base, su metadata es Base.metadata
sqla_metadata = Base.metadata 

db_backend = SQLAlchemyBackend(
    database_url=DATABASE_URL,
    metadata=sqla_metadata,
    model_mapping=model_mapping,
    echo=True # Opcional, para logging de SQL
)

async def main():
    await db_backend.connect()
    await db_backend.create_tables() # Crea las tablas si no existen

    # Ejemplo de uso:
    # new_user_data = {"username": "johndoe", "email": "john@example.com"}
    # created_user = await db_backend.create(UserPydantic, new_user_data)
    # print(f"Usuario creado: {created_user}")

    await db_backend.disconnect()

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())
```

Con esta estructura, el `SQLAlchemyBackend` puede manejar la conversión entre los datos que recibe/devuelve (Pydantic) y cómo se almacenan (SQLAlchemy).

## Gestión de Transacciones

El `SQLAlchemyBackend` ofrece control sobre las transacciones de la base de datos, lo cual es crucial para asegurar la atomicidad de las operaciones.

### Control Manual de Transacciones

Puedes controlar las transacciones manualmente utilizando los siguientes métodos:

- `await db_backend.begin_transaction()`: Inicia una nueva transacción.
- `await db_backend.commit_transaction()`: Confirma los cambios realizados dentro de la transacción actual.
- `await db_backend.rollback_transaction()`: Revierte los cambios realizados dentro de la transacción actual.

```python
# Ejemplo de control manual de transacciones
async def manual_transaction_example():
    try:
        await db_backend.begin_transaction()
        user_data = {"username": "testuser_manual", "email": "manual@example.com"}
        created_user = await db_backend.create(UserPydantic, user_data)
        # ... otras operaciones ...
        await db_backend.commit_transaction()
        print(f"Usuario creado y transacción confirmada: {created_user}")
    except Exception as e:
        print(f"Error en la transacción, revirtiendo: {e}")
        await db_backend.rollback_transaction()
```

### Gestor de Contexto para Transacciones

Para un manejo más simple y seguro de las transacciones, puedes utilizar el gestor de contexto `transaction()`:

```python
# Ejemplo con gestor de contexto
async def context_manager_transaction_example():
    try:
        async with db_backend.transaction():
            user_data = {"username": "testuser_context", "email": "context@example.com"}
            created_user = await db_backend.create(UserPydantic, user_data)
            # ... otras operaciones ...
            # Si ocurre una excepción aquí, se hará rollback automáticamente
        print(f"Usuario creado, transacción confirmada automáticamente: {created_user}")
    except Exception as e:
        # La excepción se propaga después del rollback automático
        print(f"Error capturado fuera del contexto de transacción: {e}")
```

El gestor de contexto se encarga automáticamente de hacer `commit` si el bloque se completa sin errores, o `rollback` si ocurre cualquier excepción.

## Ejecución de SQL Crudo

Para situaciones donde necesitas ejecutar consultas SQL directamente (ej. consultas muy complejas, DDL, o funciones específicas de la base de datos), el backend proporciona los siguientes métodos:

### `fetch_all_raw(query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]`

Ejecuta una consulta SQL cruda y devuelve una lista de diccionarios, donde cada diccionario representa una fila.

```python
async def fetch_all_example():
    # Asegúrate de que la tabla 'users' y los datos existan
    query = "SELECT id, username, email FROM users WHERE is_active = :active ORDER BY username"
    params = {"active": True}
    active_users = await db_backend.fetch_all_raw(query, params)
    for user in active_users:
        print(f"Usuario activo: {user['username']} ({user['email']})")
```

### `fetch_one_raw(query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]`

Ejecuta una consulta SQL cruda y devuelve un único diccionario (la primera fila) o `None` si no hay resultados.

```python
async def fetch_one_example():
    query = "SELECT id, username FROM users WHERE email = :email"
    params = {"email": "john@example.com"}
    user = await db_backend.fetch_one_raw(query, params)
    if user:
        print(f"Usuario encontrado: {user['username']}")
    else:
        print("Usuario no encontrado.")
```

### `execute_raw(query: str, params: Optional[Dict[str, Any]] = None) -> Any`

Ejecuta una sentencia SQL cruda que no se espera que devuelva filas directamente (como `INSERT`, `UPDATE`, `DELETE`, o DDL). Para sentencias DML (Data Manipulation Language), devuelve el número de filas afectadas (`rowcount`). Para DDL (Data Definition Language) u otras sentencias, el valor de retorno puede variar según el driver de la base de datos (a menudo es -1 o None si `rowcount` no es aplicable).

```python
async def execute_update_example():
    # Suponiendo que el usuario con id 1 existe
    query = "UPDATE users SET is_active = :new_status WHERE id = :user_id"
    params = {"new_status": False, "user_id": 1}
    rows_affected = await db_backend.execute_raw(query, params)
    print(f"Filas afectadas por la actualización: {rows_affected}")

    # Ejemplo de creación de una tabla (DDL)
    # try:
    #     create_table_query = """
    #     CREATE TABLE IF NOT EXISTS audit_log (
    #         id SERIAL PRIMARY KEY,
    #         action VARCHAR(255) NOT NULL,
    #         timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc')
    #     );
    #     """
    #     await db_backend.execute_raw(create_table_query)
    #     print("Tabla 'audit_log' verificada/creada.")
    # except Exception as e:
    #     print(f"Error creando tabla 'audit_log': {e}")
```

**Nota de Seguridad:** Al usar SQL crudo, ten mucho cuidado con la inyección SQL. Utiliza siempre consultas parametrizadas (pasando valores a través del argumento `params`) en lugar de formatear cadenas SQL directamente con datos de entrada del usuario.
