from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict

# --- Usuario ---
class User(BaseModel):
    id: str = Field(..., description="ID único del usuario")
    email: EmailStr = Field(..., description="Correo electrónico")
    full_name: str = Field(..., description="Nombre completo")
    is_active: bool = Field(default=True, description="¿Está activo?")
    organization_id: Optional[str] = Field(None, description="ID de la organización")
    roles: List[str] = Field(default_factory=list, description="Roles asignados")

# --- Organización ---
class Organization(BaseModel):
    id: str = Field(..., description="ID único de la organización")
    name: str = Field(..., description="Nombre de la organización")
    is_active: bool = Field(default=True, description="¿Está activa?")

# --- Agente ---
class Agent(BaseModel):
    id: str = Field(..., description="ID único del agente")
    name: str = Field(..., description="Nombre del agente")
    status: str = Field(..., description="Estado (online/offline)")
    owner_id: Optional[str] = Field(None, description="ID del usuario dueño")
    metadata: Optional[Dict[str, str]] = Field(default_factory=dict, description="Metadatos adicionales")

# --- Permisos ---
class Permission(BaseModel):
    id: str = Field(..., description="ID del permiso")
    name: str = Field(..., description="Nombre del permiso")
    description: Optional[str] = Field(None, description="Descripción")

# --- Respuesta estándar ---
class APIResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[dict] = None
