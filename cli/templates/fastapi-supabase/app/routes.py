"""
Definición de rutas para la API.

Este archivo contiene los routers y endpoints para las diferentes funcionalidades de la API.
"""

from fastapi import APIRouter, Depends, HTTPException, Body, Path, status
from typing import List, Dict, Any, Optional

from services.integrations.fastapi.supabase_fastapi import SupabaseFastAPI
from services.auth.interfaces.auth_provider import UserIdentity
from services.database.interfaces.db_adapter import DatabaseAdapter, FilterCondition, QueryOptions

from app.models import Recurso, RecursoCreate, RecursoUpdate, Usuario

# Crear routers
auth_router = APIRouter(prefix="/auth", tags=["Autenticación"])
usuarios_router = APIRouter(prefix="/usuarios", tags=["Usuarios"])
recursos_router = APIRouter(prefix="/recursos", tags=["Recursos"])

# Referencia a la integración de Supabase (se configura en main.py)
supabase = None

def configure_routes(supabase_instance: SupabaseFastAPI):
    """
    Configura las rutas con la instancia de Supabase.
    Esta función debe llamarse desde main.py después de crear la instancia.
    """
    global supabase
    supabase = supabase_instance

# --- Rutas de autenticación ---

@auth_router.post("/registro", status_code=status.HTTP_201_CREATED)
async def registro(
    data: dict = Body(...),
    request=None
):
    """
    Registra un nuevo usuario.
    
    Requiere email, password y nombre en el body.
    """
    auth_provider = supabase.get_auth_provider(request)
    db_adapter = supabase.get_db_adapter(request)
    
    try:
        # Registrar en Supabase Auth
        response = auth_provider.client.auth.sign_up({
            "email": data.get("email"),
            "password": data.get("password")
        })
        
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error al registrar usuario"
            )
        
        # Crear perfil de usuario
        await db_adapter.create(Usuario, {
            "user_id": response.user.id,
            "nombre": data.get("nombre"),
            "biografia": data.get("biografia", None)
        })
        
        return {
            "mensaje": "Usuario registrado correctamente",
            "id": response.user.id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error: {str(e)}"
        )

@auth_router.post("/login")
async def login(
    data: dict = Body(...),
    request=None
):
    """
    Inicia sesión con email y contraseña.
    
    Devuelve un token JWT para autenticación.
    """
    auth_provider = supabase.get_auth_provider(request)
    
    try:
        # Autenticar usuario
        identity = await auth_provider.authenticate({
            "auth_type": "password",
            "email": data.get("email"),
            "password": data.get("password")
        })
        
        if not identity.is_authenticated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )
        
        # Obtener sesión
        session = auth_provider.client.auth.get_session()
        
        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "token_type": "bearer",
            "user": {
                "id": identity.id,
                "email": identity.email
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error: {str(e)}"
        )

# --- Rutas de recursos ---

@recursos_router.post("/", status_code=status.HTTP_201_CREATED)
async def crear_recurso(
    data: RecursoCreate,
    current_user: UserIdentity = Depends(supabase.get_current_user),
    db: DatabaseAdapter = Depends(supabase.get_db_adapter)
):
    """
    Crea un nuevo recurso asociado al usuario autenticado.
    """
    # Crear datos con ID del usuario
    recurso_data = data.dict()
    recurso_data["usuario_id"] = current_user.id
    
    # Crear en base de datos
    recurso = await db.create(Recurso, recurso_data)
    
    return recurso

@recursos_router.get("/", response_model=List[Recurso])
async def listar_recursos(
    publico: Optional[bool] = None,
    current_user: UserIdentity = Depends(supabase.get_current_user),
    db: DatabaseAdapter = Depends(supabase.get_db_adapter)
):
    """
    Lista los recursos del usuario o los públicos.
    
    Query params:
    - publico: Si se especifica, filtra por recursos públicos/privados
    """
    # Preparar condiciones de filtrado
    conditions = []
    
    # Si se especifica estado de público, filtrar por ello
    if publico is not None:
        conditions.append(FilterCondition.equals("publico", publico))
    
    # Mostrar recursos propios y los públicos de otros
    conditions.append(
        FilterCondition.or_condition([
            FilterCondition.equals("usuario_id", current_user.id),
            FilterCondition.equals("publico", True)
        ])
    )
    
    # Ejecutar consulta
    result = await db.query(
        Recurso,
        conditions=conditions,
        options=QueryOptions(limit=100)
    )
    
    return result.data

@recursos_router.get("/{recurso_id}", response_model=Recurso)
async def obtener_recurso(
    recurso_id: str = Path(...),
    current_user: UserIdentity = Depends(supabase.get_current_user),
    db: DatabaseAdapter = Depends(supabase.get_db_adapter)
):
    """
    Obtiene un recurso específico si el usuario tiene permiso.
    """
    # Obtener el recurso
    recurso = await db.read(Recurso, recurso_id)
    
    if not recurso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurso no encontrado"
        )
    
    # Verificar permisos (propio o público)
    if recurso.usuario_id != current_user.id and not recurso.publico:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver este recurso"
        )
    
    return recurso

@recursos_router.put("/{recurso_id}", response_model=Recurso)
async def actualizar_recurso(
    recurso_id: str = Path(...),
    data: RecursoUpdate = Body(...),
    current_user: UserIdentity = Depends(supabase.get_current_user),
    db: DatabaseAdapter = Depends(supabase.get_db_adapter)
):
    """
    Actualiza un recurso si el usuario es propietario.
    """
    # Verificar existencia y propiedad
    recurso = await db.read(Recurso, recurso_id)
    
    if not recurso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurso no encontrado"
        )
    
    if recurso.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para modificar este recurso"
        )
    
    # Actualizar solo los campos proporcionados
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    updated = await db.update(Recurso, recurso_id, update_data)
    
    return updated

@recursos_router.delete("/{recurso_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_recurso(
    recurso_id: str = Path(...),
    current_user: UserIdentity = Depends(supabase.get_current_user),
    db: DatabaseAdapter = Depends(supabase.get_db_adapter)
):
    """
    Elimina un recurso si el usuario es propietario.
    """
    # Verificar existencia y propiedad
    recurso = await db.read(Recurso, recurso_id)
    
    if not recurso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurso no encontrado"
        )
    
    if recurso.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para eliminar este recurso"
        )
    
    # Eliminar recurso
    await db.delete(Recurso, recurso_id)
