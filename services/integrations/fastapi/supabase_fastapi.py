"""
Integración de Supabase con FastAPI para TauseStack.

Este módulo proporciona middleware, dependencias y utilidades para 
integrar fácilmente Supabase en aplicaciones FastAPI.
"""

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Callable, Dict, Any, Optional, Type, TypeVar, Generic, List, Union
from pydantic import BaseModel
import logging
from functools import lru_cache

from services.auth.interfaces.auth_provider import AuthProvider, UserIdentity
from services.auth.adapters.supabase_provider import SupabaseAuthProvider
from services.database.interfaces.db_adapter import DatabaseAdapter, FilterCondition, QueryOptions, QueryResult
from services.database.adapters.supabase.client import SupabaseDatabaseAdapter

# Configuración de logging
logger = logging.getLogger("tausestack.integrations.fastapi")

# Tipos genéricos para anotaciones
T = TypeVar('T', bound=BaseModel)

# Configuración del security scheme para Bearer tokens
security = HTTPBearer()

class SupabaseConfig(BaseModel):
    """Configuración para la integración de Supabase."""
    supabase_url: str
    supabase_key: str
    auto_init: bool = True
    debug_mode: bool = False

@lru_cache()
def get_supabase_config() -> SupabaseConfig:
    """
    Factory para obtener la configuración de Supabase.
    Utilizando @lru_cache para almacenar en caché la configuración.
    
    Returns:
        SupabaseConfig: Configuración de Supabase.
    """
    # En un entorno real, esto debería cargar desde variables de entorno o configuración
    return SupabaseConfig(
        supabase_url="https://tu-proyecto.supabase.co",
        supabase_key="tu-api-key-publica-de-supabase",
        auto_init=True,
        debug_mode=False
    )

class SupabaseFastAPI:
    """
    Integrador principal de Supabase con FastAPI.
    
    Proporciona middleware, dependencias y utilidades para integrar Supabase en FastAPI.
    """
    
    def __init__(
        self, 
        app: FastAPI,
        config: Optional[SupabaseConfig] = None,
        auth_provider_class: Type[AuthProvider] = SupabaseAuthProvider,
        db_adapter_class: Type[DatabaseAdapter] = SupabaseDatabaseAdapter,
    ):
        """
        Inicializa el integrador de Supabase con FastAPI.
        
        Args:
            app: Aplicación FastAPI.
            config: Configuración de Supabase (opcional).
            auth_provider_class: Clase de proveedor de autenticación.
            db_adapter_class: Clase de adaptador de base de datos.
        """
        self.app = app
        self.config = config or get_supabase_config()
        
        # Inicializar proveedores
        self.auth_provider = auth_provider_class()
        self.db_adapter = db_adapter_class()
        
        # Registrar eventos de inicio/apagado
        self._setup_lifecycle_events()
        
        # Registrar middleware si se solicita
        if self.config.auto_init:
            self._setup_middleware()
            
        logger.info(f"SupabaseFastAPI inicializado con URL: {self.config.supabase_url}")
    
    def _setup_lifecycle_events(self):
        """Configura eventos de inicio y apagado de la aplicación."""
        
        @self.app.on_event("startup")
        async def startup_supabase():
            """Inicializa los clientes de Supabase al iniciar la aplicación."""
            config_dict = {
                "supabase_url": self.config.supabase_url,
                "supabase_key": self.config.supabase_key
            }
            
            # Inicializar proveedores
            await self.auth_provider.initialize(config_dict)
            await self.db_adapter.initialize(config_dict)
            
            logger.info("Proveedores de Supabase inicializados correctamente")
        
        @self.app.on_event("shutdown")
        async def shutdown_supabase():
            """Cierra conexiones al detener la aplicación."""
            # Implementar cierre de conexiones si es necesario
            logger.info("Conexiones de Supabase cerradas correctamente")
    
    def _setup_middleware(self):
        """Configura middleware para la aplicación FastAPI."""
        
        @self.app.middleware("http")
        async def supabase_middleware(request: Request, call_next):
            """Middleware para agregar clientes de Supabase al request state."""
            # Establecer proveedores en request.state para acceso en endpoints
            request.state.auth_provider = self.auth_provider
            request.state.db_adapter = self.db_adapter
            
            # Continuar con el siguiente middleware o endpoint
            response = await call_next(request)
            return response
    
    async def get_current_user(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> UserIdentity:
        """
        Dependency para obtener el usuario actual de un token Bearer.
        
        Args:
            request: Request de FastAPI.
            credentials: Credenciales de autenticación HTTP.
            
        Returns:
            UserIdentity: Identidad del usuario autenticado.
            
        Raises:
            HTTPException: Si la autenticación falla.
        """
        try:
            token = credentials.credentials
            identity = await self.auth_provider.validate_token(token)
            
            if not identity.is_authenticated:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido o expirado",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return identity
        except Exception as e:
            logger.error(f"Error de autenticación: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Error de autenticación",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def get_db_adapter(self, request: Request) -> DatabaseAdapter:
        """
        Dependency para obtener el adaptador de base de datos.
        
        Args:
            request: Request de FastAPI.
            
        Returns:
            DatabaseAdapter: Adaptador de base de datos.
        """
        return request.state.db_adapter
    
    def get_auth_provider(self, request: Request) -> AuthProvider:
        """
        Dependency para obtener el proveedor de autenticación.
        
        Args:
            request: Request de FastAPI.
            
        Returns:
            AuthProvider: Proveedor de autenticación.
        """
        return request.state.auth_provider

    def crud_router_factory(self, model: Type[T], prefix: str, tags: List[str] = None):
        """
        Factoría para crear un router CRUD para un modelo específico.
        
        Args:
            model: Clase del modelo Pydantic.
            prefix: Prefijo para las rutas.
            tags: Etiquetas para la documentación.
            
        Returns:
            APIRouter: Router con endpoints CRUD.
        """
        from fastapi import APIRouter, Body, Path, Query, status
        
        # Crear router
        router = APIRouter(prefix=prefix, tags=tags or [model.__name__])
        
        # Crear schemas para requests
        class CreateSchema(BaseModel):
            """Schema para creación."""
            __annotations__ = {
                k: v for k, v in model.__annotations__.items() 
                if k != 'id' and not k.startswith('_')
            }
        
        class UpdateSchema(BaseModel):
            """Schema para actualización."""
            __annotations__ = {
                k: Optional[v] for k, v in model.__annotations__.items()
                if k != 'id' and not k.startswith('_')
            }
        
        # Endpoints CRUD
        @router.post("/", response_model=model, status_code=status.HTTP_201_CREATED)
        async def create_item(
            item: CreateSchema = Body(...),
            current_user: UserIdentity = Depends(self.get_current_user),
            db: DatabaseAdapter = Depends(self.get_db_adapter)
        ):
            """Crea un nuevo item."""
            # Agregar user_id si el modelo lo requiere
            data = item.dict()
            if hasattr(model, 'usuario_id') or hasattr(model, 'user_id'):
                field_name = 'usuario_id' if hasattr(model, 'usuario_id') else 'user_id'
                data[field_name] = current_user.id
            
            created = await db.create(model, data)
            return created
        
        @router.get("/", response_model=List[model])
        async def list_items(
            limit: int = Query(50, ge=1, le=100),
            offset: int = Query(0, ge=0),
            current_user: UserIdentity = Depends(self.get_current_user),
            db: DatabaseAdapter = Depends(self.get_db_adapter)
        ):
            """Lista items con paginación."""
            # Crear condición de filtro para el usuario actual si corresponde
            conditions = []
            if hasattr(model, 'usuario_id'):
                conditions.append(FilterCondition.equals('usuario_id', current_user.id))
            elif hasattr(model, 'user_id'):
                conditions.append(FilterCondition.equals('user_id', current_user.id))
            
            # Configurar opciones de consulta
            options = QueryOptions(
                limit=limit,
                offset=offset,
                include_count=True
            )
            
            # Ejecutar consulta
            result = await db.query(model, conditions, options)
            return result.data
        
        @router.get("/{item_id}", response_model=model)
        async def get_item(
            item_id: str = Path(..., title="ID del item"),
            current_user: UserIdentity = Depends(self.get_current_user),
            db: DatabaseAdapter = Depends(self.get_db_adapter)
        ):
            """Obtiene un item por su ID."""
            item = await db.read(model, item_id)
            
            if not item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{model.__name__} no encontrado"
                )
            
            # Verificar propiedad si es necesario
            if (hasattr(item, 'usuario_id') and item.usuario_id != current_user.id) or \
               (hasattr(item, 'user_id') and item.user_id != current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para acceder a este recurso"
                )
            
            return item
        
        @router.put("/{item_id}", response_model=model)
        async def update_item(
            item_id: str = Path(..., title="ID del item"),
            item: UpdateSchema = Body(...),
            current_user: UserIdentity = Depends(self.get_current_user),
            db: DatabaseAdapter = Depends(self.get_db_adapter)
        ):
            """Actualiza un item por su ID."""
            # Verificar que existe y pertenece al usuario
            existing = await db.read(model, item_id)
            
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{model.__name__} no encontrado"
                )
            
            # Verificar propiedad
            if (hasattr(existing, 'usuario_id') and existing.usuario_id != current_user.id) or \
               (hasattr(existing, 'user_id') and existing.user_id != current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para modificar este recurso"
                )
            
            # Actualizar
            updated = await db.update(model, item_id, item.dict(exclude_unset=True))
            return updated
        
        @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
        async def delete_item(
            item_id: str = Path(..., title="ID del item"),
            current_user: UserIdentity = Depends(self.get_current_user),
            db: DatabaseAdapter = Depends(self.get_db_adapter)
        ):
            """Elimina un item por su ID."""
            # Verificar que existe y pertenece al usuario
            existing = await db.read(model, item_id)
            
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{model.__name__} no encontrado"
                )
            
            # Verificar propiedad
            if (hasattr(existing, 'usuario_id') and existing.usuario_id != current_user.id) or \
               (hasattr(existing, 'user_id') and existing.user_id != current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permiso para eliminar este recurso"
                )
            
            # Eliminar
            await db.delete(model, item_id)
            return None
        
        return router
