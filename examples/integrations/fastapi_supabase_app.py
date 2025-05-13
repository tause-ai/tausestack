"""
Ejemplo de aplicación FastAPI con integración de Supabase usando TauseStack.

Este ejemplo muestra cómo crear una API RESTful completa con autenticación
y operaciones CRUD utilizando nuestras integraciones.

Para ejecutar:
1. Configura tu URL y Key de Supabase
2. Ejecuta: uvicorn examples.integrations.fastapi_supabase_app:app --reload
3. Visita http://localhost:8000/docs para ver la documentación OpenAPI
"""

import os
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Body, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

# Importaciones de TauseStack
from services.integrations.fastapi.supabase_fastapi import SupabaseFastAPI
from services.auth.interfaces.auth_provider import UserIdentity
from services.database.interfaces.db_adapter import DatabaseAdapter

# Crear aplicación FastAPI
app = FastAPI(
    title="API TauseStack con Supabase",
    description="Ejemplo de integración FastAPI con Supabase usando TauseStack",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de datos
class Nota(BaseModel):
    """Modelo para una nota personal."""
    id: Optional[UUID] = Field(None, description="ID único de la nota")
    titulo: str = Field(..., description="Título de la nota")
    contenido: str = Field(..., description="Contenido de la nota")
    etiquetas: List[str] = Field(default_factory=list, description="Lista de etiquetas")
    archivada: bool = Field(False, description="Si la nota está archivada")
    usuario_id: Optional[UUID] = Field(None, description="ID del propietario")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Perfil(BaseModel):
    """Modelo para el perfil de usuario."""
    id: Optional[UUID] = Field(None, description="ID único del perfil")
    user_id: UUID = Field(..., description="ID del usuario en auth.users")
    nombre: str = Field(..., description="Nombre completo")
    biografia: Optional[str] = Field(None, description="Biografía del usuario")
    tema_preferido: str = Field("claro", description="Tema preferido (claro/oscuro)")
    idioma: str = Field("es", description="Idioma preferido")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# Schemas para auth
class UserRegister(BaseModel):
    """Schema para registrar usuario."""
    email: str = Field(..., description="Email del usuario")
    password: str = Field(..., description="Contraseña")
    nombre: str = Field(..., description="Nombre completo")

class LoginResponse(BaseModel):
    """Schema para respuesta de login."""
    access_token: str
    refresh_token: str
    token_type: str
    user: Dict[str, Any]

# Inicializar integración con Supabase
supabase = SupabaseFastAPI(app)

# Endpoints de autenticación
@app.post("/auth/registro", status_code=status.HTTP_201_CREATED)
async def registro(
    user_data: UserRegister,
    request: Request,
):
    """Registra un nuevo usuario."""
    auth_provider = supabase.get_auth_provider(request)
    db_adapter = supabase.get_db_adapter(request)
    
    try:
        # Registrar usuario en Supabase
        response = auth_provider.client.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password
        })
        
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error al registrar el usuario"
            )
        
        # Crear perfil del usuario
        await db_adapter.create(Perfil, {
            "user_id": response.user.id,
            "nombre": user_data.nombre,
            "biografia": None,
            "tema_preferido": "claro",
            "idioma": "es"
        })
        
        return {
            "id": response.user.id,
            "email": response.user.email,
            "mensaje": "Usuario registrado correctamente. Verifica tu correo electrónico."
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al registrar: {str(e)}"
        )

@app.post("/auth/login", response_model=LoginResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
):
    """Inicia sesión utilizando email y contraseña."""
    auth_provider = supabase.get_auth_provider(request)
    
    try:
        # Autenticar usuario
        identity = await auth_provider.authenticate({
            "auth_type": "password",
            "email": form_data.username,
            "password": form_data.password
        })
        
        if not identity.is_authenticated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Obtener sesión
        session = auth_provider.client.auth.get_session()
        
        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "token_type": "bearer",
            "user": {
                "id": identity.id,
                "email": identity.email,
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error de inicio de sesión: {str(e)}"
        )

# Crear routers CRUD
notas_router = supabase.crud_router_factory(
    model=Nota, 
    prefix="/notas", 
    tags=["Notas"]
)

perfiles_router = supabase.crud_router_factory(
    model=Perfil,
    prefix="/perfil",
    tags=["Perfil"]
)

# Incluir routers en la aplicación
app.include_router(notas_router)
app.include_router(perfiles_router)

# Endpoint para obtener usuario actual
@app.get("/usuario/yo", tags=["Usuario"])
async def get_current_user(
    current_user: UserIdentity = Depends(supabase.get_current_user),
    request: Request = None,
    db: DatabaseAdapter = Depends(supabase.get_db_adapter)
):
    """Obtiene información del usuario actual."""
    # Buscar perfil
    from services.database.interfaces.db_adapter import FilterCondition, QueryOptions
    
    perfiles = await db.query(
        Perfil,
        conditions=[FilterCondition.equals("user_id", current_user.id)],
        options=QueryOptions(limit=1)
    )
    
    perfil = perfiles.data[0] if perfiles.data else None
    
    return {
        "id": current_user.id,
        "email": current_user.email,
        "perfil": perfil
    }

# Ejecutar si se llama directamente
if __name__ == "__main__":
    uvicorn.run("examples.integrations.fastapi_supabase_app:app", host="0.0.0.0", port=8000, reload=True)
