"""
Ejemplo de integración de autenticación y base de datos con Supabase en Tausestack.

Este ejemplo muestra cómo utilizar los adaptadores de Supabase para:
1. Autenticar usuarios
2. Realizar operaciones CRUD en la base de datos
3. Implementar permisos basados en Row Level Security (RLS)
"""

import asyncio
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

# Importaciones de Tausestack
from services.auth.interfaces.auth_provider import UserIdentity
from services.auth.adapters.supabase_provider import SupabaseAuthProvider
from services.database.interfaces.db_adapter import FilterCondition, QueryOptions
from services.database.adapters.supabase.client import SupabaseDatabaseAdapter

# --- Definición de modelos ---

class Tarea(BaseModel):
    """Modelo para representar una tarea."""
    id: Optional[str] = None
    titulo: str
    descripcion: Optional[str] = None
    completada: bool = False
    usuario_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Definición explícita del nombre de la tabla
    __tablename__ = "tareas"

class CrearTareaRequest(BaseModel):
    """Modelo para la solicitud de creación de tarea."""
    titulo: str
    descripcion: Optional[str] = None

class ActualizarTareaRequest(BaseModel):
    """Modelo para la solicitud de actualización de tarea."""
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    completada: Optional[bool] = None

# --- Configuración de la aplicación ---

app = FastAPI(title="Ejemplo Supabase CRUD - Tausestack")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar proveedores
auth_provider = SupabaseAuthProvider()
db_adapter = SupabaseDatabaseAdapter()

# Configuración de la aplicación
@app.on_event("startup")
async def startup_event():
    """Inicializar los adaptadores al iniciar la aplicación."""
    # En producción, obtener estas claves del sistema de secretos
    config = {
        "supabase_url": "https://tu-proyecto.supabase.co",
        "supabase_key": "tu-api-key-publica-de-supabase"
    }
    
    # Inicializar adaptador de autenticación
    await auth_provider.initialize(config)
    print("Proveedor de autenticación Supabase inicializado")
    
    # Inicializar adaptador de base de datos
    await db_adapter.initialize(config)
    print("Adaptador de base de datos Supabase inicializado")

# --- Dependencia para autenticación ---

async def get_current_user(request: Request) -> UserIdentity:
    """Obtiene el usuario actual a partir del token de autenticación."""
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

# --- Endpoints de autenticación ---

@app.post("/auth/registro")
async def registro(user_data: Dict[str, Any]):
    """Registra un nuevo usuario."""
    try:
        email = user_data.get("email")
        password = user_data.get("password")
        
        if not email or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email y contraseña son requeridos"
            )
        
        # Registrar usuario
        response = auth_provider.client.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error al registrar el usuario"
            )
        
        return {
            "id": response.user.id,
            "email": response.user.email,
            "mensaje": "Usuario registrado correctamente"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al registrar: {str(e)}"
        )

@app.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Inicia sesión usando email y contraseña."""
    try:
        # Iniciar sesión
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
        
        # Obtener tokens
        session = auth_provider.client.auth.get_session()
        
        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "token_type": "bearer",
            "usuario": {
                "id": identity.id,
                "email": identity.email
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error de inicio de sesión: {str(e)}"
        )

# --- Endpoints CRUD para tareas ---

@app.post("/api/tareas")
async def crear_tarea(
    data: CrearTareaRequest,
    current_user: UserIdentity = Depends(get_current_user)
):
    """Crea una nueva tarea para el usuario actual."""
    try:
        # Crear la tarea con el ID del usuario actual
        tarea_data = {
            "titulo": data.titulo,
            "descripcion": data.descripcion,
            "usuario_id": current_user.id
        }
        
        tarea = await db_adapter.create(Tarea, tarea_data)
        
        return {
            "mensaje": "Tarea creada correctamente",
            "tarea": tarea
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear tarea: {str(e)}"
        )

@app.get("/api/tareas")
async def listar_tareas(
    completada: Optional[bool] = None,
    current_user: UserIdentity = Depends(get_current_user)
):
    """Lista las tareas del usuario actual, con filtro opcional por estado."""
    try:
        # Filtrar por usuario_id (seguridad)
        conditions = [
            FilterCondition.equals("usuario_id", current_user.id)
        ]
        
        # Filtro opcional por estado de completada
        if completada is not None:
            conditions.append(FilterCondition.equals("completada", completada))
        
        # Configurar opciones de consulta
        options = QueryOptions(
            order_by="created_at",
            order_direction="desc",
            include_count=True
        )
        
        # Ejecutar consulta
        resultado = await db_adapter.query(Tarea, conditions, options)
        
        return {
            "tareas": [tarea.dict() for tarea in resultado.data],
            "total": resultado.count
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar tareas: {str(e)}"
        )

@app.get("/api/tareas/{tarea_id}")
async def obtener_tarea(
    tarea_id: str,
    current_user: UserIdentity = Depends(get_current_user)
):
    """Obtiene una tarea específica del usuario actual."""
    try:
        # Obtener la tarea
        tarea = await db_adapter.read(Tarea, tarea_id)
        
        if not tarea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea no encontrada"
            )
        
        # Verificar que la tarea pertenece al usuario (seguridad)
        if tarea.usuario_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver esta tarea"
            )
        
        return tarea
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener tarea: {str(e)}"
        )

@app.put("/api/tareas/{tarea_id}")
async def actualizar_tarea(
    tarea_id: str,
    data: ActualizarTareaRequest,
    current_user: UserIdentity = Depends(get_current_user)
):
    """Actualiza una tarea específica del usuario actual."""
    try:
        # Primero, verificar que la tarea existe y pertenece al usuario
        tarea_actual = await db_adapter.read(Tarea, tarea_id)
        
        if not tarea_actual:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea no encontrada"
            )
        
        if tarea_actual.usuario_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para modificar esta tarea"
            )
        
        # Preparar datos de actualización
        update_data = {}
        if data.titulo is not None:
            update_data["titulo"] = data.titulo
        if data.descripcion is not None:
            update_data["descripcion"] = data.descripcion
        if data.completada is not None:
            update_data["completada"] = data.completada
        
        # Actualizar la tarea
        tarea_actualizada = await db_adapter.update(Tarea, tarea_id, update_data)
        
        return {
            "mensaje": "Tarea actualizada correctamente",
            "tarea": tarea_actualizada
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar tarea: {str(e)}"
        )

@app.delete("/api/tareas/{tarea_id}")
async def eliminar_tarea(
    tarea_id: str,
    current_user: UserIdentity = Depends(get_current_user)
):
    """Elimina una tarea específica del usuario actual."""
    try:
        # Primero, verificar que la tarea existe y pertenece al usuario
        tarea_actual = await db_adapter.read(Tarea, tarea_id)
        
        if not tarea_actual:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea no encontrada"
            )
        
        if tarea_actual.usuario_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para eliminar esta tarea"
            )
        
        # Eliminar la tarea
        eliminada = await db_adapter.delete(Tarea, tarea_id)
        
        if not eliminada:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar la tarea"
            )
        
        return {
            "mensaje": "Tarea eliminada correctamente"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar tarea: {str(e)}"
        )

# --- Configuración de la base de datos en Supabase ---

"""
-- Script SQL para configurar la tabla en Supabase

-- Crear tabla de tareas
CREATE TABLE tareas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    titulo TEXT NOT NULL,
    descripcion TEXT,
    completada BOOLEAN DEFAULT FALSE,
    usuario_id UUID NOT NULL REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Configurar Row Level Security (RLS)
ALTER TABLE tareas ENABLE ROW LEVEL SECURITY;

-- Política: los usuarios solo pueden ver sus propias tareas
CREATE POLICY "Usuarios pueden ver sus propias tareas" ON tareas
    FOR SELECT USING (auth.uid() = usuario_id);

-- Política: los usuarios solo pueden insertar sus propias tareas
CREATE POLICY "Usuarios pueden insertar sus propias tareas" ON tareas
    FOR INSERT WITH CHECK (auth.uid() = usuario_id);

-- Política: los usuarios solo pueden actualizar sus propias tareas
CREATE POLICY "Usuarios pueden actualizar sus propias tareas" ON tareas
    FOR UPDATE USING (auth.uid() = usuario_id);

-- Política: los usuarios solo pueden eliminar sus propias tareas
CREATE POLICY "Usuarios pueden eliminar sus propias tareas" ON tareas
    FOR DELETE USING (auth.uid() = usuario_id);

-- Función para actualizar el campo updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para actualizar el campo updated_at
CREATE TRIGGER set_updated_at
BEFORE UPDATE ON tareas
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();
"""

# Punto de entrada para ejecutar directamente con Python
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
