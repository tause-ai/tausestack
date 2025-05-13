"""
Ejemplo de modelos Pydantic para generar migraciones Supabase.

Este archivo contiene modelos de ejemplo para demostrar cómo el generador
de migraciones crea automáticamente el esquema SQL optimizado para Supabase.

Para generar la migración, ejecuta:
python -m services.database.migrations.cli examples/database/modelo_migracion.py --output migracion.sql
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class Perfil(BaseModel):
    """Perfil de usuario con información personal."""
    id: Optional[UUID] = Field(None, description="ID único del perfil")
    user_id: UUID = Field(..., description="ID del usuario en auth.users")
    nombre: str = Field(..., description="Nombre completo")
    biografia: Optional[str] = Field(None, description="Biografía del usuario")
    foto_url: Optional[str] = Field(None, description="URL de la foto de perfil")
    verificado: bool = Field(False, description="Si el perfil está verificado")
    
    # Nombre explícito de tabla
    __tablename__ = "perfiles"

class Categoria(BaseModel):
    """Categoría para clasificar contenido."""
    id: Optional[UUID] = Field(None, description="ID único de la categoría")
    nombre: str = Field(..., description="Nombre de la categoría", unique=True)
    descripcion: Optional[str] = Field(None, description="Descripción de la categoría")
    icono: Optional[str] = Field(None, description="Nombre del icono")
    color: Optional[str] = Field("#3B82F6", description="Color en formato hexadecimal")
    orden: int = Field(0, description="Orden de visualización")

class Proyecto(BaseModel):
    """Proyecto creado por un usuario."""
    id: Optional[UUID] = Field(None, description="ID único del proyecto")
    titulo: str = Field(..., description="Título del proyecto")
    descripcion: str = Field(..., description="Descripción del proyecto")
    contenido: Dict[str, Any] = Field(default_factory=dict, description="Contenido JSON del proyecto")
    usuario_id: UUID = Field(..., description="ID del usuario propietario")
    categoria_id: Optional[UUID] = Field(None, description="ID de la categoría")
    publico: bool = Field(False, description="Si el proyecto es público")
    destacado: bool = Field(False, description="Si el proyecto está destacado")
    metadatos: Dict[str, Any] = Field(default_factory=dict, description="Metadatos adicionales")
    
    # Configurar RLS personalizada
    class Config:
        rls_policies = [
            # Permitir que los administradores vean todos los proyectos
            {
                "name": "Los administradores pueden ver todos los proyectos",
                "operation": "SELECT",
                "using": "auth.uid() IN (SELECT id FROM perfiles WHERE rol = 'admin')"
            },
            # Permitir que los usuarios vean proyectos públicos o propios
            {
                "name": "Usuarios pueden ver proyectos públicos o propios",
                "operation": "SELECT",
                "using": "publico = true OR auth.uid() = usuario_id"
            }
        ]

class Colaboracion(BaseModel):
    """Colaboración entre un usuario y un proyecto."""
    id: Optional[UUID] = Field(None, description="ID único de la colaboración")
    proyecto_id: UUID = Field(..., description="ID del proyecto")
    usuario_id: UUID = Field(..., description="ID del usuario colaborador")
    rol: str = Field("editor", description="Rol del colaborador (viewer, editor, admin)")
    invitado_por: UUID = Field(..., description="ID del usuario que invitó")
    aceptada: bool = Field(False, description="Si la invitación fue aceptada")
    fecha_invitacion: datetime = Field(default_factory=datetime.now, description="Fecha de invitación")
    
    # Índices personalizados
    class Config:
        indices = [
            {"columns": ["proyecto_id", "usuario_id"], "unique": True},
            {"columns": ["usuario_id"], "unique": False},
            {"columns": ["proyecto_id"], "unique": False}
        ]

class Comentario(BaseModel):
    """Comentario en un proyecto."""
    id: Optional[UUID] = Field(None, description="ID único del comentario")
    proyecto_id: UUID = Field(..., description="ID del proyecto comentado")
    usuario_id: UUID = Field(..., description="ID del usuario que comenta")
    contenido: str = Field(..., description="Texto del comentario")
    respuesta_a_id: Optional[UUID] = Field(None, description="ID del comentario al que responde")
    editado: bool = Field(False, description="Si el comentario fue editado")
    
    # No generar timestamps para esta tabla
    __timestamps__ = False
