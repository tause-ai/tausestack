"""
Modelos de datos para la aplicación.

Este archivo contiene los modelos Pydantic que representan las entidades 
de la base de datos y los schemas para validación de datos.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

# Modelos de base de datos

class Usuario(BaseModel):
    """Modelo de usuario."""
    id: Optional[UUID] = Field(None, description="ID único del usuario")
    user_id: UUID = Field(..., description="ID del usuario en auth.users")
    nombre: str = Field(..., description="Nombre completo")
    biografia: Optional[str] = Field(None, description="Biografía del usuario")
    es_admin: bool = Field(False, description="Si el usuario es administrador")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Nombre explícito de tabla
    __tablename__ = "usuarios"

class Recurso(BaseModel):
    """Modelo para recursos genéricos."""
    id: Optional[UUID] = Field(None, description="ID único del recurso")
    titulo: str = Field(..., description="Título del recurso")
    descripcion: str = Field(..., description="Descripción del recurso")
    usuario_id: UUID = Field(..., description="ID del propietario")
    datos: Dict[str, Any] = Field(default_factory=dict, description="Datos adicionales")
    publico: bool = Field(False, description="Si el recurso es público")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# Schemas para API

class UsuarioCreate(BaseModel):
    """Schema para crear usuario."""
    email: EmailStr = Field(..., description="Correo electrónico")
    password: str = Field(..., min_length=8, description="Contraseña")
    nombre: str = Field(..., min_length=2, description="Nombre completo")

class UsuarioResponse(BaseModel):
    """Schema para respuesta de usuario."""
    id: UUID
    nombre: str
    email: EmailStr
    biografia: Optional[str] = None
    es_admin: bool = False

class LoginRequest(BaseModel):
    """Schema para solicitud de login."""
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    """Schema para respuesta de login."""
    access_token: str
    token_type: str
    user: UsuarioResponse

class RecursoCreate(BaseModel):
    """Schema para crear recurso."""
    titulo: str = Field(..., min_length=3, max_length=100)
    descripcion: str
    datos: Dict[str, Any] = Field(default_factory=dict)
    publico: bool = False

class RecursoUpdate(BaseModel):
    """Schema para actualizar recurso."""
    titulo: Optional[str] = Field(None, min_length=3, max_length=100)
    descripcion: Optional[str] = None
    datos: Optional[Dict[str, Any]] = None
    publico: Optional[bool] = None
