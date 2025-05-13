"""
Ejemplo de uso del AuthProvider JWT en una aplicación FastAPI.

Este ejemplo muestra cómo implementar autenticación JWT en una API
utilizando las interfaces abstractas de Tausestack.
"""

import asyncio
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import uvicorn
from typing import Dict, Any, Optional

# Importar las interfaces y adaptador de Tausestack
from services.auth.interfaces.auth_provider import UserIdentity
from services.auth.adapters.jwt_provider import JWTAuthProvider

# Crear aplicación FastAPI
app = FastAPI(title="Ejemplo Auth Tausestack")

# Inicializar proveedor JWT
auth_provider = JWTAuthProvider()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# Base de datos simulada (en producción usar una DB real)
users_db = {
    "usuario1": {
        "id": "1",
        "username": "usuario1",
        "email": "usuario1@ejemplo.com",
        "password": "password1",  # En producción: hash seguro
        "roles": ["admin"],
        "permissions": ["users:read", "users:write"]
    },
    "usuario2": {
        "id": "2",
        "username": "usuario2",
        "email": "usuario2@ejemplo.com",
        "password": "password2",  # En producción: hash seguro
        "roles": ["user"],
        "permissions": ["users:read"]
    }
}

# Función de inicialización
@app.on_event("startup")
async def startup_event():
    """Inicializa el proveedor de autenticación al iniciar la aplicación."""
    # En producción, obtener la clave de un sistema seguro de secretos
    await auth_provider.initialize({
        "secret_key": "mi_clave_secreta_super_segura_para_dev_123",
        "access_token_expire_minutes": 15
    })
    print("Proveedor de autenticación JWT inicializado")

# Dependencia para obtener el usuario actual
async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserIdentity:
    """Obtiene el usuario actual a partir del token JWT."""
    identity = await auth_provider.validate_token(token)
    if not identity.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return identity

# Endpoint de autenticación
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Endpoint para obtener un token JWT mediante credenciales."""
    # Verificar credenciales (en producción usar hash seguro)
    user = users_db.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generar token de acceso
    access_token = await auth_provider.generate_token(
        user["id"],
        username=user["username"],
        email=user["email"],
        roles=user["roles"],
        permissions=user["permissions"]
    )

    # Generar token de refresco (más largo)
    refresh_token = await auth_provider.generate_token(
        user["id"],
        type="refresh",
        username=user["username"]
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

# Endpoint protegido
@app.get("/users/me")
async def get_user_profile(current_user: UserIdentity = Depends(get_current_user)):
    """Endpoint protegido que requiere autenticación."""
    return current_user.to_dict()

# Endpoint de refresco de token
@app.post("/token/refresh")
async def refresh(refresh_token: str):
    """Refresca un token JWT expirado."""
    try:
        tokens = await auth_provider.refresh_token(refresh_token)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

# Endpoint de cierre de sesión
@app.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    """Revoca un token JWT."""
    success = await auth_provider.revoke_token(token)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al cerrar sesión"
        )
    return {"message": "Sesión cerrada correctamente"}

# Punto de entrada para ejecutar directamente con Python
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
