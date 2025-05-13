"""
Interfaces abstractas para adaptadores de bases de datos.

Este módulo define las interfaces base que todos los adaptadores de bases de datos
deben implementar, independientemente de la tecnología específica (PostgreSQL, MySQL, etc).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, TypeVar, Generic, Type
from pydantic import BaseModel

# Tipo genérico para modelos
T = TypeVar('T', bound=BaseModel)

class FilterCondition:
    """
    Representa una condición de filtrado para consultas de bases de datos.
    """
    
    def __init__(
        self,
        field: str,
        operator: str,
        value: Any
    ):
        """
        Args:
            field: Campo sobre el que se aplica la condición.
            operator: Operador de comparación ("eq", "gt", "lt", "contains", etc.).
            value: Valor contra el que se compara.
        """
        self.field = field
        self.operator = operator
        self.value = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la condición a un diccionario."""
        return {
            "field": self.field,
            "operator": self.operator,
            "value": self.value
        }
    
    @staticmethod
    def equals(field: str, value: Any) -> 'FilterCondition':
        """Crea una condición de igualdad."""
        return FilterCondition(field, "eq", value)
    
    @staticmethod
    def greater_than(field: str, value: Union[int, float, str]) -> 'FilterCondition':
        """Crea una condición 'mayor que'."""
        return FilterCondition(field, "gt", value)
    
    @staticmethod
    def less_than(field: str, value: Union[int, float, str]) -> 'FilterCondition':
        """Crea una condición 'menor que'."""
        return FilterCondition(field, "lt", value)
    
    @staticmethod
    def contains(field: str, value: str) -> 'FilterCondition':
        """Crea una condición 'contiene'."""
        return FilterCondition(field, "contains", value)
    
    @staticmethod
    def in_list(field: str, values: List[Any]) -> 'FilterCondition':
        """Crea una condición 'está en la lista'."""
        return FilterCondition(field, "in", values)


class QueryOptions:
    """
    Opciones para consultas de bases de datos.
    """
    
    def __init__(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
        order_direction: Optional[str] = "asc",
        include_count: bool = False,
        include_relations: Optional[List[str]] = None
    ):
        """
        Args:
            limit: Número máximo de resultados.
            offset: Número de resultados a saltar.
            order_by: Campo por el que ordenar.
            order_direction: Dirección de ordenación ("asc" o "desc").
            include_count: Si se debe incluir el conteo total de resultados.
            include_relations: Relaciones a incluir en los resultados.
        """
        self.limit = limit
        self.offset = offset
        self.order_by = order_by
        self.order_direction = order_direction
        self.include_count = include_count
        self.include_relations = include_relations or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte las opciones a un diccionario."""
        return {
            "limit": self.limit,
            "offset": self.offset,
            "order_by": self.order_by,
            "order_direction": self.order_direction,
            "include_count": self.include_count,
            "include_relations": self.include_relations
        }


class QueryResult(Generic[T]):
    """
    Resultado de una consulta a la base de datos.
    """
    
    def __init__(
        self,
        data: List[T],
        count: Optional[int] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ):
        """
        Args:
            data: Lista de resultados.
            count: Número total de resultados (sin aplicar limit/offset).
            limit: Límite aplicado a la consulta.
            offset: Offset aplicado a la consulta.
        """
        self.data = data
        self.count = count
        self.limit = limit
        self.offset = offset
    
    @property
    def has_more(self) -> bool:
        """Indica si hay más resultados disponibles."""
        if self.count is None or self.limit is None:
            return False
        return (self.offset or 0) + len(self.data) < self.count


class DatabaseAdapter(ABC, Generic[T]):
    """
    Interfaz abstracta para adaptadores de bases de datos.
    
    Esta clase define el contrato que todos los adaptadores de bases de datos
    deben implementar, independientemente de la tecnología específica.
    """
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Inicializa el adaptador con la configuración proporcionada.
        
        Args:
            config: Configuración específica del adaptador.
            
        Returns:
            bool: True si la inicialización fue exitosa.
        """
        pass
    
    @abstractmethod
    async def create(self, model_class: Type[T], data: Dict[str, Any]) -> T:
        """
        Crea un nuevo registro en la base de datos.
        
        Args:
            model_class: Clase del modelo Pydantic.
            data: Datos a insertar.
            
        Returns:
            T: Instancia del modelo creado.
        """
        pass
    
    @abstractmethod
    async def read(self, model_class: Type[T], id: Any) -> Optional[T]:
        """
        Lee un registro por su ID.
        
        Args:
            model_class: Clase del modelo Pydantic.
            id: Identificador único del registro.
            
        Returns:
            Optional[T]: Instancia del modelo si existe, None si no.
        """
        pass
    
    @abstractmethod
    async def update(self, model_class: Type[T], id: Any, data: Dict[str, Any]) -> Optional[T]:
        """
        Actualiza un registro existente.
        
        Args:
            model_class: Clase del modelo Pydantic.
            id: Identificador único del registro.
            data: Datos a actualizar.
            
        Returns:
            Optional[T]: Instancia del modelo actualizado si existe.
        """
        pass
    
    @abstractmethod
    async def delete(self, model_class: Type[T], id: Any) -> bool:
        """
        Elimina un registro existente.
        
        Args:
            model_class: Clase del modelo Pydantic.
            id: Identificador único del registro.
            
        Returns:
            bool: True si se eliminó correctamente.
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def execute_raw(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Ejecuta una consulta raw/nativa en la base de datos.
        
        Args:
            query: Consulta en el lenguaje nativo de la BD.
            params: Parámetros para la consulta.
            
        Returns:
            Any: Resultado de la consulta.
        """
        pass
    
    @abstractmethod
    async def begin_transaction(self) -> str:
        """
        Inicia una transacción.
        
        Returns:
            str: ID de la transacción.
        """
        pass
    
    @abstractmethod
    async def commit_transaction(self, transaction_id: str) -> bool:
        """
        Confirma una transacción.
        
        Args:
            transaction_id: ID de la transacción a confirmar.
            
        Returns:
            bool: True si se confirmó correctamente.
        """
        pass
    
    @abstractmethod
    async def rollback_transaction(self, transaction_id: str) -> bool:
        """
        Revierte una transacción.
        
        Args:
            transaction_id: ID de la transacción a revertir.
            
        Returns:
            bool: True si se revirtió correctamente.
        """
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """
        Cierra la conexión con la base de datos.
        """
        pass
