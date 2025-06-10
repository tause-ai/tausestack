# Tausestack SDK - Auth Main Logic

import os
import json
from typing import Optional, Type, Any

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
            project_id = os.getenv("TAUSESTACK_FIREBASE_PROJECT_ID")
            key_path = os.getenv("TAUSESTACK_FIREBASE_SERVICE_ACCOUNT_KEY_PATH")
            key_json_str = os.getenv("TAUSESTACK_FIREBASE_SERVICE_ACCOUNT_JSON")

            service_account_creds: Any = None
            if key_json_str:
                try:
                    service_account_creds = json.loads(key_json_str)
                except json.JSONDecodeError as e:
                    raise AuthException(
                        f"Error al parsear TAUSESTACK_FIREBASE_SERVICE_ACCOUNT_JSON: {e}"
                    )
            elif key_path:
                service_account_creds = key_path
            else:
                raise AuthException(
                    "Se debe configurar TAUSESTACK_FIREBASE_SERVICE_ACCOUNT_KEY_PATH o "
                    "TAUSESTACK_FIREBASE_SERVICE_ACCOUNT_JSON para el backend de Firebase."
                )
            
            try:
                _auth_backend_instance = FirebaseAuthBackend(
                    service_account_key_path=service_account_creds if isinstance(service_account_creds, str) else None,
                    service_account_key_dict=service_account_creds if isinstance(service_account_creds, dict) else None,
                    project_id=project_id
                )
            except ValueError as ve:
                raise AuthException(f"Error de configuración de FirebaseAuthBackend: {ve}")
            except Exception as e:
                 raise AuthException(f"No se pudo inicializar FirebaseAuthBackend: {e}")

        else:
            raise NotImplementedError(
                f"Backend de autenticación '{backend_type}' no implementado o no configurado en TAUSESTACK_AUTH_BACKEND."
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
