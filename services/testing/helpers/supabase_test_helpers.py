"""
Helpers para testing de integraciones con Supabase.

Estos helpers permiten realizar pruebas con datos reales en Supabase,
pero de manera controlada y aislada para evitar afectar datos de producción.
"""

import os
import uuid
import asyncio
import inspect
from typing import Dict, Any, Optional, List, Type, TypeVar, Callable, AsyncGenerator
from pydantic import BaseModel
import pytest
from contextlib import asynccontextmanager

# Importaciones de TauseStack
from services.auth.adapters.supabase_provider import SupabaseAuthProvider
from services.database.adapters.supabase.client import SupabaseDatabaseAdapter
from services.database.interfaces.db_adapter import FilterCondition

# Tipo genérico para anotaciones
T = TypeVar('T', bound=BaseModel)

class SupabaseTestConfig(BaseModel):
    """Configuración para las pruebas con Supabase."""
    supabase_url: str
    supabase_key: str
    test_email: str = "test@example.com"
    test_password: str = "Test123456!"
    cleanup_after_tests: bool = True
    prefix_test_tables: bool = True
    table_prefix: str = "test_"

def get_test_config() -> SupabaseTestConfig:
    """
    Obtiene la configuración para testing desde variables de entorno.
    
    Returns:
        SupabaseTestConfig: Configuración para las pruebas.
    """
    # En pruebas reales, estas vendrían de variables de entorno o archivo .env
    return SupabaseTestConfig(
        supabase_url=os.environ.get("SUPABASE_TEST_URL", "https://tu-proyecto-test.supabase.co"),
        supabase_key=os.environ.get("SUPABASE_TEST_KEY", "tu-api-key-de-test"),
        test_email=os.environ.get("SUPABASE_TEST_EMAIL", "test@example.com"),
        test_password=os.environ.get("SUPABASE_TEST_PASSWORD", "Test123456!"),
        cleanup_after_tests=os.environ.get("CLEANUP_TESTS", "true").lower() == "true",
        prefix_test_tables=os.environ.get("PREFIX_TEST_TABLES", "true").lower() == "true"
    )

class SupabaseTestClient:
    """
    Cliente Supabase para testing que gestiona la limpieza de datos.
    
    Permite crear datos de prueba y asegura que sean eliminados
    después de ejecutar las pruebas para no contaminar el entorno.
    """
    
    def __init__(self, config: Optional[SupabaseTestConfig] = None):
        """
        Inicializa el cliente de pruebas.
        
        Args:
            config: Configuración para las pruebas.
        """
        self.config = config or get_test_config()
        self.auth_provider = SupabaseAuthProvider()
        self.db_adapter = SupabaseDatabaseAdapter()
        self.test_session_id = str(uuid.uuid4())
        self.created_resources: Dict[str, List[Dict[str, Any]]] = {}
        self._initialized = False
    
    async def initialize(self):
        """Inicializa los adaptadores de Supabase."""
        if self._initialized:
            return
        
        config_dict = {
            "supabase_url": self.config.supabase_url,
            "supabase_key": self.config.supabase_key
        }
        
        await self.auth_provider.initialize(config_dict)
        await self.db_adapter.initialize(config_dict)
        
        self._initialized = True
    
    async def cleanup(self):
        """Limpia todos los recursos creados durante las pruebas."""
        if not self.config.cleanup_after_tests:
            return
        
        # Eliminar en orden inverso para respetar dependencias
        for model_name, resources in reversed(list(self.created_resources.items())):
            for resource in resources:
                if "id" in resource:
                    try:
                        # Intentar eliminar el recurso
                        await self.db_adapter.delete_raw(
                            table_name=model_name,
                            id=resource["id"]
                        )
                    except Exception as e:
                        print(f"Error al eliminar {model_name} con ID {resource['id']}: {str(e)}")
    
    async def create_test_user(self) -> Dict[str, Any]:
        """
        Crea un usuario de prueba o utiliza uno existente.
        
        Returns:
            Dict[str, Any]: Datos del usuario creado.
        """
        try:
            # Intentar registrar un nuevo usuario con correo único
            unique_email = f"test.{uuid.uuid4()}@example.com"
            
            response = self.auth_provider.client.auth.sign_up({
                "email": unique_email,
                "password": self.config.test_password
            })
            
            if not response.user:
                raise Exception("No se pudo crear usuario de prueba")
            
            # Registrar para limpieza
            if "users" not in self.created_resources:
                self.created_resources["users"] = []
            
            self.created_resources["users"].append({"id": response.user.id})
            
            return {
                "id": response.user.id,
                "email": unique_email,
                "password": self.config.test_password
            }
        except Exception as e:
            print(f"Error al crear usuario de prueba: {str(e)}")
            # Intentar iniciar sesión con usuario predeterminado
            return {
                "email": self.config.test_email,
                "password": self.config.test_password
            }
    
    async def login_test_user(self, credentials: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Inicia sesión con un usuario de prueba.
        
        Args:
            credentials: Credenciales del usuario (o usa las predeterminadas).
            
        Returns:
            Dict[str, Any]: Datos de sesión del usuario.
        """
        if not credentials:
            credentials = {
                "email": self.config.test_email,
                "password": self.config.test_password
            }
        
        # Autenticar usuario
        identity = await self.auth_provider.authenticate({
            "auth_type": "password",
            "email": credentials["email"],
            "password": credentials["password"]
        })
        
        if not identity.is_authenticated:
            raise Exception("Falló la autenticación del usuario de prueba")
        
        # Obtener tokens
        session = self.auth_provider.client.auth.get_session()
        
        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "user_id": identity.id,
            "email": identity.email
        }
    
    async def create_test_data(self, model_class: Type[T], data: Dict[str, Any]) -> T:
        """
        Crea datos de prueba y los registra para limpieza posterior.
        
        Args:
            model_class: Clase del modelo Pydantic.
            data: Datos a insertar.
            
        Returns:
            T: Instancia del modelo creado.
        """
        # Determinar nombre de tabla
        table_name = _get_table_name(model_class)
        
        # Aplicar prefijo si está configurado
        if self.config.prefix_test_tables:
            table_name = f"{self.config.table_prefix}{table_name}"
        
        # Agregar identificador de sesión de prueba para facilitar limpieza
        data["_test_session_id"] = self.test_session_id
        
        # Crear datos en Supabase
        created = await self.db_adapter.create(model_class, data)
        
        # Registrar para limpieza
        if table_name not in self.created_resources:
            self.created_resources[table_name] = []
        
        self.created_resources[table_name].append({"id": getattr(created, "id")})
        
        return created

def _get_table_name(model_class: Type[BaseModel]) -> str:
    """
    Obtiene el nombre de la tabla a partir de la clase del modelo.
    
    Args:
        model_class: Clase del modelo Pydantic.
        
    Returns:
        str: Nombre de la tabla.
    """
    # Buscar atributo explícito __tablename__
    if hasattr(model_class, "__tablename__"):
        return getattr(model_class, "__tablename__")
    
    # Convertir CamelCase a snake_case
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
async def supabase_test_client() -> AsyncGenerator[SupabaseTestClient, None]:
    """
    Contexto para utilizar cliente de Supabase en tests.
    
    Yields:
        SupabaseTestClient: Cliente inicializado para testing.
    """
    client = SupabaseTestClient()
    await client.initialize()
    
    try:
        yield client
    finally:
        await client.cleanup()

# Decoradores para tests con pytest
def supabase_fixture():
    """
    Fixture de pytest para proporcionar un cliente Supabase para pruebas.
    
    Returns:
        Callable: Decorador para pruebas.
    """
    @pytest.fixture
    async def _supabase_fixture():
        """
        Fixture que proporciona un cliente Supabase inicializado.
        
        Returns:
            SupabaseTestClient: Cliente para pruebas.
        """
        async with supabase_test_client() as client:
            yield client
    
    return _supabase_fixture

def with_test_user():
    """
    Fixture de pytest para proporcionar un usuario de prueba autenticado.
    
    Returns:
        Callable: Decorador para pruebas.
    """
    @pytest.fixture
    async def _test_user_fixture(supabase):
        """
        Fixture que proporciona un usuario de prueba autenticado.
        
        Args:
            supabase: Cliente Supabase (inyectado por pytest).
            
        Returns:
            Dict[str, Any]: Datos del usuario y sesión.
        """
        user = await supabase.create_test_user()
        session = await supabase.login_test_user(user)
        return {**user, **session}
    
    return _test_user_fixture

# Ejemplo de uso en un test
"""
import pytest
from services.testing.helpers.supabase_test_helpers import supabase_fixture, with_test_user

# Definir fixtures
supabase = supabase_fixture()
test_user = with_test_user()

@pytest.mark.asyncio
async def test_crear_nota(supabase, test_user):
    # Crear datos de prueba
    nota = await supabase.create_test_data(Nota, {
        "titulo": "Nota de prueba",
        "contenido": "Contenido de prueba",
        "usuario_id": test_user["user_id"]
    })
    
    # Verificar que se creó correctamente
    assert nota.id is not None
    assert nota.titulo == "Nota de prueba"
    
    # No es necesario limpiar, se hace automáticamente al finalizar el test
"""
