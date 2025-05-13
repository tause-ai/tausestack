"""
Ejemplo de uso del SupabaseAuthProvider en una aplicación FastAPI.

Este ejemplo muestra cómo implementar autenticación con Supabase
utilizando las interfaces abstractas de Tausestack.
"""

import asyncio
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Dict, Any, Optional

# Importar las interfaces y adaptador de Tausestack
from services.auth.interfaces.auth_provider import UserIdentity
from services.auth.adapters.supabase_provider import SupabaseAuthProvider

# Crear aplicación FastAPI
app = FastAPI(title="Ejemplo Supabase Auth - Tausestack")

# Configurar CORS para aplicaciones frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, restringir a dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar proveedor Supabase
auth_provider = SupabaseAuthProvider()

# Función de inicialización
@app.on_event("startup")
async def startup_event():
    """Inicializa el proveedor de autenticación al iniciar la aplicación."""
    # En producción, obtener estas claves del sistema de secretos
    await auth_provider.initialize({
        "supabase_url": "https://tu-proyecto.supabase.co",
        "supabase_key": "tu-api-key-publica-de-supabase"
    })
    print("Proveedor de autenticación Supabase inicializado")

# Dependencia para obtener el usuario actual
async def get_current_user(request: Request) -> UserIdentity:
    """Obtiene el usuario actual a partir del token de autenticación."""
    # Extraer token del header Authorization
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no proporcionado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_header.split(" ")[1]
    identity = await auth_provider.validate_token(token)
    
    if not identity.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return identity

# Endpoint de registro
@app.post("/auth/register")
async def register(user_data: Dict[str, Any]):
    """
    Registra un nuevo usuario en Supabase.
    
    Ejemplo:
    {
        "email": "usuario@ejemplo.com",
        "password": "contraseña123",
        "user_metadata": {
            "nombre": "Usuario Ejemplo",
            "apellido": "Apellido Ejemplo"
        }
    }
    """
    try:
        email = user_data.get("email")
        password = user_data.get("password")
        metadata = user_data.get("user_metadata", {})
        
        if not email or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email y contraseña son requeridos"
            )
        
        # Registrar usuario usando el cliente Supabase directamente
        # ya que AuthProvider no tiene método de registro estándar
        response = auth_provider.client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": metadata
            }
        })
        
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error al registrar el usuario"
            )
        
        return {
            "id": response.user.id,
            "email": response.user.email,
            "message": "Usuario registrado correctamente"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al registrar: {str(e)}"
        )

# Endpoint de login
@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Inicia sesión usando email y contraseña."""
    try:
        # Usar el método authenticate del proveedor
        identity = await auth_provider.authenticate({
            "auth_type": "password",
            "email": form_data.username,  # OAuth2PasswordRequestForm usa username para el email
            "password": form_data.password
        })
        
        if not identity.is_authenticated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Obtener tokens de la sesión actual
        session = auth_provider.client.auth.get_session()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al obtener la sesión"
            )
        
        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "token_type": "bearer",
            "user": {
                "id": identity.id,
                "email": identity.email,
                "roles": identity.roles
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error de inicio de sesión: {str(e)}"
        )

# Endpoint para enviar magic link
@app.post("/auth/magic-link")
async def send_magic_link(data: Dict[str, str]):
    """Envía un magic link al email proporcionado."""
    try:
        email = data.get("email")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email es requerido"
            )
        
        # Usar el método authenticate con tipo magic_link
        identity = await auth_provider.authenticate({
            "auth_type": "magic_link",
            "email": email
        })
        
        return {
            "message": f"Se ha enviado un enlace de inicio de sesión a {email}",
            "status": "pending"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al enviar magic link: {str(e)}"
        )

# Endpoint para refrescar token
@app.post("/auth/refresh")
async def refresh_token(data: Dict[str, str]):
    """Refresca un token de acceso usando el refresh token."""
    try:
        refresh_token = data.get("refresh_token")
        
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token es requerido"
            )
        
        tokens = await auth_provider.refresh_token(refresh_token)
        
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al refrescar token: {str(e)}"
        )

# Endpoint para cerrar sesión
@app.post("/auth/logout")
async def logout(request: Request):
    """Cierra la sesión del usuario."""
    try:
        # Extraer token del header Authorization
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token no proporcionado"
            )
        
        token = auth_header.split(" ")[1]
        
        # Revocar token
        success = await auth_provider.revoke_token(token)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al cerrar sesión"
            )
        
        return {"message": "Sesión cerrada correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cerrar sesión: {str(e)}"
        )

# Endpoint protegido
@app.get("/api/perfil")
async def get_user_profile(current_user: UserIdentity = Depends(get_current_user)):
    """Endpoint protegido que requiere autenticación."""
    return current_user.to_dict()

# Punto de entrada para ejecutar directamente con Python
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
