"""
Adaptador de base de datos Supabase para Tausestack.

Este módulo implementa la interfaz DatabaseAdapter utilizando Supabase
como backend de base de datos, aprovechando PostgreSQL y sus capacidades.
"""

import uuid
import json
from typing import Dict, Any, List, Optional, Union, TypeVar, Generic, Type
from datetime import datetime

from supabase import create_client, Client
from pydantic import BaseModel

from ...interfaces.db_adapter import (
    DatabaseAdapter,
    FilterCondition,
    QueryOptions,
    QueryResult
)

# Tipo genérico para modelos
T = TypeVar('T', bound=BaseModel)

class SupabaseDatabaseAdapter(DatabaseAdapter[T]):
    """
    Implementación de DatabaseAdapter que utiliza Supabase como backend.
    
    Esta clase proporciona acceso a la base de datos PostgreSQL de Supabase,
    gestionando operaciones CRUD, consultas y transacciones.
    """
    
    def __init__(self):
        self.supabase_url = None
        self.supabase_key = None
        self.client = None
        self.active_transactions = {}
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Inicializa el adaptador con la configuración proporcionada.
        
        Args:
            config: Configuración que incluye supabase_url, supabase_key, etc.
            
        Returns:
            bool: True si la inicialización fue exitosa.
        """
        try:
            self.supabase_url = config.get("supabase_url")
            self.supabase_key = config.get("supabase_key")
            
            if not self.supabase_url or not self.supabase_key:
                return False
                
            # Crear cliente de Supabase
            self.client = create_client(self.supabase_url, self.supabase_key)
            
            return True
        except Exception:
            return False
    
    async def create(self, model_class: Type[T], data: Dict[str, Any]) -> T:
        """
        Crea un nuevo registro en la tabla correspondiente al modelo.
        
        Args:
            model_class: Clase del modelo Pydantic.
            data: Datos a insertar.
            
        Returns:
            T: Instancia del modelo creado.
            
        Raises:
            ValueError: Si ocurre un error al crear el registro.
        """
        try:
            # Obtener el nombre de la tabla a partir del modelo
            table_name = self._get_table_name(model_class)
            
            # Si no hay ID, generar uno
            if "id" not in data:
                data["id"] = str(uuid.uuid4())
            
            # Añadir timestamps si no están presentes
            current_time = datetime.utcnow().isoformat()
            if "created_at" not in data:
                data["created_at"] = current_time
            if "updated_at" not in data:
                data["updated_at"] = current_time
            
            # Insertar en la tabla
            response = self.client.table(table_name).insert(data).execute()
            
            if hasattr(response, "error") and response.error:
                raise ValueError(f"Error al crear registro: {response.error}")
            
            # Obtener el registro creado
            created_data = response.data[0] if response.data else None
            
            if not created_data:
                raise ValueError("No se pudo obtener el registro creado")
            
            # Convertir a modelo Pydantic
            return model_class(**created_data)
        except Exception as e:
            raise ValueError(f"Error al crear registro: {str(e)}")
    
    async def read(self, model_class: Type[T], id: Any) -> Optional[T]:
        """
        Lee un registro por su ID.
        
        Args:
            model_class: Clase del modelo Pydantic.
            id: Identificador único del registro.
            
        Returns:
            Optional[T]: Instancia del modelo si existe, None si no.
        """
        try:
            # Obtener el nombre de la tabla a partir del modelo
            table_name = self._get_table_name(model_class)
            
            # Consultar registro por ID
            response = self.client.table(table_name).select("*").eq("id", id).execute()
            
            if hasattr(response, "error") and response.error:
                return None
            
            # Verificar si hay resultados
            if not response.data or len(response.data) == 0:
                return None
            
            # Convertir a modelo Pydantic
            return model_class(**response.data[0])
        except Exception:
            return None
    
    async def update(self, model_class: Type[T], id: Any, data: Dict[str, Any]) -> Optional[T]:
        """
        Actualiza un registro existente.
        
        Args:
            model_class: Clase del modelo Pydantic.
            id: Identificador único del registro.
            data: Datos a actualizar.
            
        Returns:
            Optional[T]: Instancia del modelo actualizado si existe.
            
        Raises:
            ValueError: Si ocurre un error al actualizar el registro.
        """
        try:
            # Obtener el nombre de la tabla a partir del modelo
            table_name = self._get_table_name(model_class)
            
            # Actualizar timestamp
            data["updated_at"] = datetime.utcnow().isoformat()
            
            # Actualizar registro
            response = self.client.table(table_name).update(data).eq("id", id).execute()
            
            if hasattr(response, "error") and response.error:
                raise ValueError(f"Error al actualizar registro: {response.error}")
            
            # Verificar si hay resultados
            if not response.data or len(response.data) == 0:
                return None
            
            # Convertir a modelo Pydantic
            return model_class(**response.data[0])
        except Exception as e:
            raise ValueError(f"Error al actualizar registro: {str(e)}")
    
    async def delete(self, model_class: Type[T], id: Any) -> bool:
        """
        Elimina un registro existente.
        
        Args:
            model_class: Clase del modelo Pydantic.
            id: Identificador único del registro.
            
        Returns:
            bool: True si se eliminó correctamente.
        """
        try:
            # Obtener el nombre de la tabla a partir del modelo
            table_name = self._get_table_name(model_class)
            
            # Eliminar registro
            response = self.client.table(table_name).delete().eq("id", id).execute()
            
            if hasattr(response, "error") and response.error:
                return False
            
            # Verificar si se eliminó algún registro
            return response.data and len(response.data) > 0
        except Exception:
            return False
    
    async def query(
        self,
        model_class: Type[T],
        conditions: Optional[List[FilterCondition]] = None,
        options: Optional[QueryOptions] = None
    ) -> QueryResult[T]:
        """
        Consulta registros aplicando filtros y opciones.
        
        Args:
            model_class: Clase del modelo Pydantic.
            conditions: Lista de condiciones de filtrado.
            options: Opciones de consulta (límite, orden, etc.).
            
        Returns:
            QueryResult[T]: Resultado de la consulta.
        """
        try:
            # Obtener el nombre de la tabla a partir del modelo
            table_name = self._get_table_name(model_class)
            options = options or QueryOptions()
            
            # Si se requiere el conteo, primero hacer una consulta de conteo
            count = None
            if options.include_count:
                try:
                    count_query = self.client.table(table_name).select("id", count="exact")
                    count_query = self._apply_conditions(count_query, conditions)
                    count_result = count_query.execute()
                    count = count_result.count if hasattr(count_result, "count") else None
                except Exception:
                    pass
            
            # Construir la consulta principal
            query = self.client.table(table_name).select("*")
            
            # Aplicar condiciones de filtrado
            query = self._apply_conditions(query, conditions)
            
            # Aplicar orden
            if options.order_by:
                direction = options.order_direction.lower() == "desc"
                query = query.order(options.order_by, desc=direction)
            
            # Aplicar paginación
            if options.limit is not None:
                query = query.limit(options.limit)
            if options.offset is not None:
                query = query.range(options.offset, options.offset + (options.limit or 1000) - 1)
            
            # Ejecutar consulta
            response = query.execute()
            
            if hasattr(response, "error") and response.error:
                return QueryResult(data=[], count=0)
            
            # Convertir resultados a modelos Pydantic
            result_data = [model_class(**item) for item in response.data]
            
            return QueryResult(
                data=result_data,
                count=count,
                limit=options.limit,
                offset=options.offset
            )
        except Exception as e:
            # En caso de error, devolver un resultado vacío
            return QueryResult(data=[], count=0)
    
    async def execute_raw(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Ejecuta una consulta SQL directa en PostgreSQL.
        
        Args:
            query: Consulta SQL.
            params: Parámetros para la consulta.
            
        Returns:
            Any: Resultado de la consulta.
            
        Raises:
            ValueError: Si ocurre un error al ejecutar la consulta.
        """
        try:
            # Ejecutar consulta SQL a través de la función rpc
            # Nota: esto requiere una función en Supabase que ejecute SQL arbitrario
            # lo cual puede ser un riesgo de seguridad
            raise NotImplementedError(
                "La ejecución de SQL arbitrario no está disponible en este adaptador "
                "por razones de seguridad. Usa las funciones CRUD estándar o "
                "configura funciones RPC seguras en tu proyecto Supabase."
            )
        except NotImplementedError:
            raise
        except Exception as e:
            raise ValueError(f"Error al ejecutar consulta: {str(e)}")
    
    async def begin_transaction(self) -> str:
        """
        Supabase no tiene una API de transacciones directa.
        Este método simula el inicio de una transacción.
        
        Returns:
            str: ID de la transacción simulada.
            
        Raises:
            NotImplementedError: Si las transacciones no están implementadas.
        """
        # Nota: PostgreSQL en Supabase soporta transacciones, pero
        # el cliente de Supabase no tiene una API directa para ellas
        raise NotImplementedError(
            "Las transacciones no están disponibles directamente en el cliente de Supabase. "
            "Para operaciones transaccionales, usa funciones RPC en el servidor."
        )
    
    async def commit_transaction(self, transaction_id: str) -> bool:
        """
        Confirma una transacción simulada.
        
        Args:
            transaction_id: ID de la transacción a confirmar.
            
        Returns:
            bool: True si se confirmó correctamente.
            
        Raises:
            NotImplementedError: Si las transacciones no están implementadas.
        """
        raise NotImplementedError(
            "Las transacciones no están disponibles directamente en el cliente de Supabase."
        )
    
    async def rollback_transaction(self, transaction_id: str) -> bool:
        """
        Revierte una transacción simulada.
        
        Args:
            transaction_id: ID de la transacción a revertir.
            
        Returns:
            bool: True si se revirtió correctamente.
            
        Raises:
            NotImplementedError: Si las transacciones no están implementadas.
        """
        raise NotImplementedError(
            "Las transacciones no están disponibles directamente en el cliente de Supabase."
        )
    
    async def close(self) -> None:
        """
        Cierra la conexión con Supabase.
        """
        # No hay necesidad de cerrar explícitamente la conexión con Supabase
        pass
    
    def _get_table_name(self, model_class: Type[T]) -> str:
        """
        Obtiene el nombre de la tabla a partir de la clase del modelo.
        
        Args:
            model_class: Clase del modelo Pydantic.
            
        Returns:
            str: Nombre de la tabla.
        """
        # Por convención, usar el nombre de la clase en minúsculas y plural
        # Si el modelo tiene un atributo __tablename__, usarlo
        if hasattr(model_class, "__tablename__"):
            return getattr(model_class, "__tablename__")
        
        # Por defecto, convierte CamelCase a snake_case y pluraliza
        class_name = model_class.__name__
        # Convertir CamelCase a snake_case
        snake_case = ''.join(['_'+c.lower() if c.isupper() else c for c in class_name]).lstrip('_')
        # Pluralizar (regla simple)
        if snake_case.endswith('y'):
            return snake_case[:-1] + 'ies'
        elif snake_case.endswith('s'):
            return snake_case
        else:
            return snake_case + 's'
    
    def _apply_conditions(self, query, conditions: Optional[List[FilterCondition]]):
        """
        Aplica condiciones de filtrado a una consulta.
        
        Args:
            query: Consulta de Supabase.
            conditions: Lista de condiciones de filtrado.
            
        Returns:
            Consulta con filtros aplicados.
        """
        if not conditions:
            return query
        
        for condition in conditions:
            operator = condition.operator.lower()
            field = condition.field
            value = condition.value
            
            if operator == "eq":
                query = query.eq(field, value)
            elif operator == "neq":
                query = query.neq(field, value)
            elif operator == "gt":
                query = query.gt(field, value)
            elif operator == "gte":
                query = query.gte(field, value)
            elif operator == "lt":
                query = query.lt(field, value)
            elif operator == "lte":
                query = query.lte(field, value)
            elif operator == "like":
                query = query.like(field, value)
            elif operator == "ilike":
                query = query.ilike(field, value)
            elif operator == "in":
                query = query.in_(field, value)
            elif operator == "contains":
                # Para arrays o JSONB
                query = query.contains(field, value)
            elif operator == "range":
                # Para rangos entre dos valores
                if isinstance(value, list) and len(value) == 2:
                    query = query.gte(field, value[0]).lte(field, value[1])
            elif operator == "is":
                # Para NULL/NOT NULL
                if value is None:
                    query = query.is_(field, "null")
                elif isinstance(value, bool):
                    query = query.is_(field, "true" if value else "false")
        
        return query
