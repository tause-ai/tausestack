# Tausestack SDK - Auth Main Logic

import os
import json
from typing import Optional, Type, Any, List

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .base import AbstractAuthBackend, User
from .exceptions import (
    AuthException,
    InvalidTokenException,
    UserNotFoundException,
    AccountDisabledException,
    InsufficientPermissionsException 
)
from .backends.firebase_admin import FirebaseAuthBackend, FirebaseVerifiedToken

# Variable global para almacenar la instancia del backend de autenticación configurado
_auth_backend_instance: Optional[AbstractAuthBackend] = None

# Esquema de seguridad Bearer para FastAPI
bearer_scheme = HTTPBearer(auto_error=False) 

def get_auth_backend() -> AbstractAuthBackend:
    """
    Retorna la instancia configurada del backend de autenticación.
    Inicializa el backend si aún no se ha hecho, leyendo la configuración de variables de entorno.
    """
    global _auth_backend_instance
    if _auth_backend_instance is None:
        backend_type = os.getenv("TAUSESTACK_AUTH_BACKEND", "firebase").lower()

        if backend_type == "firebase":
            # FirebaseAuthBackend ahora maneja la carga de credenciales desde:
            # 1. Argumentos directos (si se pasaran aquí, pero no es necesario)
            # 2. Variables de entorno (TAUSESTACK_FIREBASE_SA_KEY_PATH)
            # 3. SDK Secrets (TAUSESTACK_FIREBASE_SA_KEY_JSON)
            # El project_id también puede ser inferido de las credenciales o configurado vía TAUSESTACK_FIREBASE_PROJECT_ID si es necesario.
            project_id_env = os.getenv("TAUSESTACK_FIREBASE_PROJECT_ID")
            try:
                # Pasamos project_id_env explícitamente si está definido, sino FirebaseAuthBackend intentará inferirlo.
                _auth_backend_instance = FirebaseAuthBackend(project_id=project_id_env)
            except ValueError as ve: # Captura errores de configuración de credenciales desde el constructor
                raise AuthException(f"Error de configuración de FirebaseAuthBackend: {ve}")
            except AuthException: # Re-lanzar AuthExceptions del constructor
                raise
            except Exception as e:
                 raise AuthException(f"No se pudo inicializar FirebaseAuthBackend: {e}")
        # Aquí se podrían añadir otros tipos de backend (ej. 'oauth', 'dummy') en el futuro
        # elif backend_type == "otro_backend":
        # _auth_backend_instance = OtroAuthBackendConfigurado()
        else:
            raise NotImplementedError(
                f"Backend de autenticación '{backend_type}' no implementado. Configure TAUSESTACK_AUTH_BACKEND."
            )
    
    if not _auth_backend_instance:
        raise AuthException("No se pudo obtener una instancia del backend de autenticación.")
        
    return _auth_backend_instance

async def get_current_user(
    token: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> User:
    """
    Dependencia de FastAPI para obtener el usuario autenticado a partir de un token Bearer.
    Lanza HTTPException si el token es inválido, el usuario no se encuentra o está deshabilitado.
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se proporcionó token de autenticación.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    auth_backend = get_auth_backend()
    try:
        verified_token = await auth_backend.verify_token(token.credentials)
        user = await auth_backend.get_user_from_token(verified_token)
        
        if user is None:
            raise UserNotFoundException("Usuario no encontrado a partir del token.")
        
        if user.disabled:
            raise AccountDisabledException("La cuenta de usuario está deshabilitada.")
            
        return user
    except InvalidTokenException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except AccountDisabledException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=str(e)
        )
    except UserNotFoundException as e: 
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AuthException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=f"Error de autenticación: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor durante la autenticación."
        )

def require_user(required_roles: Optional[List[str]] = None):
    """
    Fábrica para crear una dependencia de FastAPI que requiere un usuario autenticado
    y, opcionalmente, verifica si tiene roles específicos.

    Args:
        required_roles: Una lista opcional de strings de roles requeridos.
                        Si un usuario tiene CUALQUIERA de los roles, se le permite el acceso.

    Returns:
        Una dependencia de FastAPI que puedes usar en tus endpoints.
    """

    async def _verify_roles(user: User = Depends(get_current_user)) -> User:
        """
        Dependencia interna que se inyecta en el endpoint y verifica los roles.
        """
        if not required_roles:
            # Si no se especifican roles, solo se requiere autenticación.
            return user

        user_roles = user.custom_claims.get("roles", [])
        if not isinstance(user_roles, list):
            # Si 'roles' en los claims no es una lista, tratar como si no tuviera roles.
            user_roles = []

        # Comprobar si el usuario tiene al menos uno de los roles requeridos.
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes los permisos necesarios para realizar esta acción.",
            )

        return user

    return _verify_roles


async def get_optional_current_user(
    token: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Optional[User]:
    """
    Dependencia de FastAPI para obtener el usuario autenticado si se proporciona un token Bearer.
    Retorna None si no hay token o si el token es inválido (sin lanzar HTTPException directamente).
    Útil para endpoints que pueden ser accedidos anónimamente o por usuarios autenticados.
    """
    if token is None:
        return None
    
    try:
        return await get_current_user(token)
    except HTTPException:
        return None
