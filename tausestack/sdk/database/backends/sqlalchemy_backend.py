from typing import Any, Dict, List, Optional, Type
from typing import Any, Dict, List, Optional, Type
from sqlalchemy import MetaData # Importar MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
# from sqlalchemy.future import select # No se usa aún, se puede quitar por ahora si no se usa en connect/disconnect
from pydantic import BaseModel

from tausestack.sdk.database.base import AbstractDatabaseBackend, Model, ItemID
from tausestack.sdk.database.exceptions import (
    ConnectionException,
    # QueryExecutionException, # No se usa aún
    # RecordNotFoundException, # No se usa aún
    SchemaException,
    # TransactionException # No se usa aún
)

class SQLAlchemyBackend(AbstractDatabaseBackend):
    """
    Implementación de AbstractDatabaseBackend utilizando SQLAlchemy.
    """

    def __init__(self, database_url: str, metadata: MetaData, echo: bool = False):
        self.database_url = database_url
        self.engine = create_async_engine(database_url, echo=echo)
        self.async_session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.metadata = metadata # Almacenar la metadata proporcionada

    async def connect(self) -> None:
        """Establece la conexión e intenta una operación simple para verificar."""
        try:
            async with self.engine.connect() as connection:
                # Realizar una prueba de conexión simple (no bloqueante si es posible)
                # Para asyncpg, una simple query puede ser 'SELECT 1'
                # Para run_sync, una función lambda vacía es suficiente para probar la conectividad básica del pool.
                await connection.run_sync(lambda sync_conn: None) 
            print(f"Conectado exitosamente a la base de datos: {self.database_url.split('@')[-1] if '@' in self.database_url else self.database_url}") # Evitar loguear creds
        except Exception as e:
            # Loguear solo el tipo de error y parte de la URL para no exponer credenciales
            db_identifier = self.database_url.split('@')[-1] if '@' in self.database_url else self.database_url
            print(f"Error al conectar a la base de datos {db_identifier}: {type(e).__name__} - {e}")
            raise ConnectionException(f"No se pudo conectar a la base de datos {db_identifier}: {e}") from e

    async def disconnect(self) -> None:
        """Cierra la conexión con la base de datos (dispose del engine)."""
        await self.engine.dispose()
        db_identifier = self.database_url.split('@')[-1] if '@' in self.database_url else self.database_url
        print(f"Desconectado de la base de datos: {db_identifier}")

    async def create_tables(self, models: Optional[List[Type[Model]]] = None) -> None:
        """
        Crea todas las tablas definidas en la metadata proporcionada durante la inicialización.
        El argumento `models` (Pydantic models) no se usa directamente aquí, ya que operamos
        sobre la metadata de SQLAlchemy.
        """
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(self.metadata.create_all)
            print("Tablas creadas (si no existían) basadas en la metadata proporcionada.")
        except Exception as e:
            raise SchemaException(f"Error al crear tablas: {e}") from e

    async def drop_tables(self, models: Optional[List[Type[Model]]] = None) -> None:
        """
        Elimina todas las tablas definidas en la metadata proporcionada.
        El argumento `models` (Pydantic models) no se usa directamente aquí.
        """
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(self.metadata.drop_all)
            print("Tablas eliminadas basadas en la metadata proporcionada.")
        except Exception as e:
            raise SchemaException(f"Error al eliminar tablas: {e}") from e

    async def create(self, model_cls: Type[Model], data: Dict[str, Any]) -> Model:
        raise NotImplementedError("create no está implementado aún.")

    async def get_by_id(self, model_cls: Type[Model], item_id: ItemID) -> Optional[Model]:
        raise NotImplementedError("get_by_id no está implementado aún.")

    async def update(self, model_cls: Type[Model], item_id: ItemID, data: Dict[str, Any]) -> Optional[Model]:
        raise NotImplementedError("update no está implementado aún.")

    async def delete(self, model_cls: Type[Model], item_id: ItemID) -> bool:
        raise NotImplementedError("delete no está implementado aún.")

    async def find(
        self,
        model_cls: Type[Model],
        filters: Optional[Dict[str, Any]] = None,
        offset: int = 0,
        limit: Optional[int] = 100,
        sort_by: Optional[List[str]] = None
    ) -> List[Model]:
        raise NotImplementedError("find no está implementado aún.")

    async def count(
        self,
        model_cls: Type[Model],
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        raise NotImplementedError("count no está implementado aún.")

    async def begin_transaction(self) -> None:
        # SQLAlchemy maneja las transacciones a nivel de sesión.
        # Esta podría ser una no-op o preparar un contexto de sesión si es necesario.
        pass

    async def commit_transaction(self) -> None:
        # Se llamaría después de operaciones dentro de una sesión.
        # La sesión debe ser manejada externamente o este método debe tener acceso a ella.
        raise NotImplementedError("commit_transaction no está implementado aún. Las sesiones deben manejarse.")

    async def rollback_transaction(self) -> None:
        raise NotImplementedError("rollback_transaction no está implementado aún. Las sesiones deben manejarse.")

    async def execute_raw(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        raise NotImplementedError("execute_raw no está implementado aún.")

    async def fetch_all_raw(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError("fetch_all_raw no está implementado aún.")

    async def fetch_one_raw(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("fetch_one_raw no está implementado aún.")
