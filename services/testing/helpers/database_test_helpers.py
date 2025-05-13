"""
Helpers para testing de bases de datos en TauseStack.

Proporciona utilidades para probar operaciones de base de datos
con datos reales pero en un entorno controlado.
"""

import uuid
import asyncio
import inspect
from typing import Dict, Any, List, Optional, Type, TypeVar, Callable, AsyncGenerator, Union
from pydantic import BaseModel
import pytest
from contextlib import asynccontextmanager

from services.database.interfaces.db_adapter import DatabaseAdapter, FilterCondition, QueryOptions

# Tipo genérico para anotaciones
T = TypeVar('T', bound=BaseModel)

class DatabaseTestContext:
    """
    Contexto para ejecutar pruebas de base de datos.
    
    Mantiene registro de todos los datos creados durante las pruebas
    para facilitar la limpieza al finalizar.
    """
    
    def __init__(self, db_adapter: DatabaseAdapter):
        """
        Inicializa el contexto de pruebas.
        
        Args:
            db_adapter: Adaptador de base de datos a utilizar.
        """
        self.db_adapter = db_adapter
        self.test_session_id = str(uuid.uuid4())
        self.created_records: Dict[str, List[Dict[str, Any]]] = {}
    
    async def create_record(self, model_class: Type[T], data: Dict[str, Any]) -> T:
        """
        Crea un registro para pruebas y lo marca para limpieza.
        
        Args:
            model_class: Clase del modelo Pydantic.
            data: Datos del registro.
            
        Returns:
            T: Modelo creado.
        """
        # Añadir marcador de sesión de prueba
        data["_test_session"] = self.test_session_id
        
        # Crear registro
        record = await self.db_adapter.create(model_class, data)
        
        # Registrar para limpieza
        table_name = get_table_name(model_class)
        if table_name not in self.created_records:
            self.created_records[table_name] = []
        
        self.created_records[table_name].append({"id": getattr(record, "id", None)})
        
        return record
    
    async def bulk_create(self, model_class: Type[T], data_list: List[Dict[str, Any]]) -> List[T]:
        """
        Crea múltiples registros para pruebas.
        
        Args:
            model_class: Clase del modelo Pydantic.
            data_list: Lista de datos para crear.
            
        Returns:
            List[T]: Lista de modelos creados.
        """
        results = []
        for data in data_list:
            record = await self.create_record(model_class, data)
            results.append(record)
        return results
    
    async def find_by_field(
        self, 
        model_class: Type[T], 
        field_name: str, 
        field_value: Any
    ) -> Optional[T]:
        """
        Busca un registro por un campo específico.
        
        Args:
            model_class: Clase del modelo Pydantic.
            field_name: Nombre del campo.
            field_value: Valor del campo.
            
        Returns:
            Optional[T]: Modelo encontrado o None.
        """
        conditions = [FilterCondition.equals(field_name, field_value)]
        result = await self.db_adapter.query(
            model_class, 
            conditions=conditions,
            options=QueryOptions(limit=1)
        )
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        
        return None
    
    async def cleanup(self):
        """Elimina todos los registros creados durante las pruebas."""
        # Procesar en orden inverso para respetar dependencias
        for table, records in reversed(list(self.created_records.items())):
            for record in records:
                if "id" in record and record["id"]:
                    try:
                        await self.db_adapter.delete_raw(table, record["id"])
                    except Exception as e:
                        print(f"Error limpiando registro de prueba: {str(e)}")
    
    async def cleanup_by_session(self):
        """
        Limpia todos los registros marcados con el ID de sesión.
        
        Útil para limpiar registros incluso si no fueron registrados explícitamente.
        """
        # Obtener lista de tablas
        tables = await self.db_adapter.list_tables()
        
        for table in tables:
            try:
                # Buscar registros con nuestra marca de sesión
                conditions = [FilterCondition.equals("_test_session", self.test_session_id)]
                await self.db_adapter.delete_by_conditions(table, conditions)
            except Exception:
                # Ignorar errores si la tabla no tiene este campo
                pass

def get_table_name(model_class: Type[BaseModel]) -> str:
    """
    Obtiene el nombre de tabla para un modelo.
    
    Args:
        model_class: Clase del modelo Pydantic.
        
    Returns:
        str: Nombre de la tabla.
    """
    if hasattr(model_class, "__tablename__"):
        return getattr(model_class, "__tablename__")
    
    # Convertir CamelCase a snake_case y pluralizar
    class_name = model_class.__name__
    snake_case = ''.join(['_'+c.lower() if c.isupper() else c for c in class_name]).lstrip('_')
    
    # Pluralizar (regla simple)
    if snake_case.endswith('y'):
        return snake_case[:-1] + 'ies'
    elif snake_case.endswith('s'):
        return snake_case
    else:
        return snake_case + 's'

@asynccontextmanager
async def database_test_context(db_adapter: DatabaseAdapter) -> AsyncGenerator[DatabaseTestContext, None]:
    """
    Contexto para pruebas de base de datos.
    
    Args:
        db_adapter: Adaptador de base de datos inicializado.
        
    Yields:
        DatabaseTestContext: Contexto para pruebas.
    """
    context = DatabaseTestContext(db_adapter)
    try:
        yield context
    finally:
        await context.cleanup()

class TestDataFactory:
    """
    Factoría para generar datos de prueba.
    
    Permite crear fácilmente datos con valores predeterminados
    pero personalizables para las pruebas.
    """
    
    def __init__(self, db_test_context: DatabaseTestContext):
        """
        Inicializa la factoría.
        
        Args:
            db_test_context: Contexto de pruebas de base de datos.
        """
        self.context = db_test_context
    
    async def create_user_profile(self, **kwargs) -> Dict[str, Any]:
        """
        Crea un perfil de usuario para pruebas.
        
        Args:
            **kwargs: Campos personalizados.
            
        Returns:
            Dict[str, Any]: Datos del perfil creado.
        """
        # Importar aquí para evitar dependencias circulares
        from your_app.models import Perfil
        
        # Datos por defecto
        data = {
            "user_id": str(uuid.uuid4()),
            "nombre": f"Usuario de prueba {uuid.uuid4().hex[:8]}",
            "biografia": "Perfil creado para testing",
            "tema_preferido": "claro",
            "idioma": "es"
        }
        
        # Sobrescribir con kwargs
        data.update(kwargs)
        
        # Crear en BD
        perfil = await self.context.create_record(Perfil, data)
        
        return {
            "id": getattr(perfil, "id", None),
            "user_id": getattr(perfil, "user_id", None),
            "nombre": getattr(perfil, "nombre", None)
        }
    
    async def create_note(self, usuario_id: str = None, **kwargs) -> Dict[str, Any]:
        """
        Crea una nota para pruebas.
        
        Args:
            usuario_id: ID del usuario propietario.
            **kwargs: Campos personalizados.
            
        Returns:
            Dict[str, Any]: Datos de la nota creada.
        """
        # Importar aquí para evitar dependencias circulares
        from your_app.models import Nota
        
        if not usuario_id:
            usuario_id = str(uuid.uuid4())
        
        # Datos por defecto
        data = {
            "titulo": f"Nota de prueba {uuid.uuid4().hex[:8]}",
            "contenido": "Contenido generado para testing",
            "usuario_id": usuario_id,
            "etiquetas": ["test", "automático"],
            "archivada": False
        }
        
        # Sobrescribir con kwargs
        data.update(kwargs)
        
        # Crear en BD
        nota = await self.context.create_record(Nota, data)
        
        return {
            "id": getattr(nota, "id", None),
            "titulo": getattr(nota, "titulo", None),
            "usuario_id": getattr(nota, "usuario_id", None)
        }

# Fixtures para pytest

@pytest.fixture
async def db_context(db_adapter):
    """
    Fixture que proporciona un contexto de pruebas de base de datos.
    
    Args:
        db_adapter: Adaptador de base de datos (inyectado por pytest).
        
    Returns:
        DatabaseTestContext: Contexto de pruebas.
    """
    async with database_test_context(db_adapter) as context:
        yield context

@pytest.fixture
def test_data_factory(db_context):
    """
    Fixture que proporciona una factoría de datos de prueba.
    
    Args:
        db_context: Contexto de pruebas (inyectado por pytest).
        
    Returns:
        TestDataFactory: Factoría de datos.
    """
    return TestDataFactory(db_context)

# Ejemplo de uso en un test
"""
import pytest
from services.testing.helpers.database_test_helpers import db_context, test_data_factory
from your_app.models import Nota

@pytest.mark.asyncio
async def test_buscar_notas(db_context, test_data_factory):
    # Crear un usuario y algunas notas
    usuario = await test_data_factory.create_user_profile()
    
    await test_data_factory.create_note(usuario_id=usuario["user_id"], titulo="Primera nota")
    await test_data_factory.create_note(usuario_id=usuario["user_id"], titulo="Segunda nota")
    
    # Buscar notas del usuario
    from services.database.interfaces.db_adapter import FilterCondition, QueryOptions
    
    result = await db_context.db_adapter.query(
        Nota,
        conditions=[FilterCondition.equals("usuario_id", usuario["user_id"])],
        options=QueryOptions(limit=10)
    )
    
    # Verificar resultados
    assert len(result.data) == 2
    assert any(nota.titulo == "Primera nota" for nota in result.data)
    assert any(nota.titulo == "Segunda nota" for nota in result.data)
"""
