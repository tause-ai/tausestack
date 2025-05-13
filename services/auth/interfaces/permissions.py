"""
Interfaces abstractas para sistemas de permisos y autorización.

Este módulo define las interfaces base para gestionar permisos, roles y autorización
en aplicaciones que usan Tausestack, independiente del mecanismo de almacenamiento.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Set, Union


class Permission:
    """
    Representación de un permiso individual en el sistema.
    """
    
    def __init__(
        self,
        id: str,
        name: str,
        resource: str,
        action: str,
        description: Optional[str] = None
    ):
        self.id = id
        self.name = name
        self.resource = resource  # ej: "users", "projects", "payments"
        self.action = action  # ej: "read", "write", "delete"
        self.description = description
    
    def __str__(self):
        return f"{self.resource}:{self.action}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el permiso a un diccionario."""
        return {
            "id": self.id,
            "name": self.name,
            "resource": self.resource,
            "action": self.action,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Permission':
        """Crea una instancia desde un diccionario."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            resource=data.get("resource", ""),
            action=data.get("action", ""),
            description=data.get("description")
        )


class Role:
    """
    Representación de un rol en el sistema, que agrupa permisos.
    """
    
    def __init__(
        self,
        id: str,
        name: str,
        permissions: List[Union[Permission, str]] = None,
        description: Optional[str] = None
    ):
        self.id = id
        self.name = name
        self.permissions = permissions or []
        self.description = description
    
    def add_permission(self, permission: Union[Permission, str]):
        """Añade un permiso al rol."""
        if permission not in self.permissions:
            self.permissions.append(permission)
    
    def remove_permission(self, permission: Union[Permission, str]):
        """Elimina un permiso del rol."""
        if permission in self.permissions:
            self.permissions.remove(permission)
    
    def has_permission(self, permission: Union[Permission, str]) -> bool:
        """Verifica si el rol tiene un permiso específico."""
        return permission in self.permissions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el rol a un diccionario."""
        perm_list = []
        for perm in self.permissions:
            if isinstance(perm, Permission):
                perm_list.append(perm.to_dict())
            else:
                perm_list.append(perm)
                
        return {
            "id": self.id,
            "name": self.name,
            "permissions": perm_list,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Role':
        """Crea una instancia desde un diccionario."""
        perms = []
        for perm in data.get("permissions", []):
            if isinstance(perm, dict):
                perms.append(Permission.from_dict(perm))
            else:
                perms.append(perm)
                
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            permissions=perms,
            description=data.get("description")
        )


class PermissionManager(ABC):
    """
    Interfaz abstracta para gestionar permisos y roles.
    
    Esta clase define el contrato que todos los gestores de permisos deben implementar,
    independientemente del mecanismo de almacenamiento (DB, archivos, etc).
    """
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Inicializa el gestor con la configuración proporcionada.
        
        Args:
            config: Configuración específica del gestor.
            
        Returns:
            bool: True si la inicialización fue exitosa.
        """
        pass
    
    @abstractmethod
    async def create_permission(self, permission: Permission) -> Permission:
        """
        Crea un nuevo permiso en el sistema.
        
        Args:
            permission: Permiso a crear.
            
        Returns:
            Permission: Permiso creado con ID asignado.
        """
        pass
    
    @abstractmethod
    async def get_permission(self, permission_id: str) -> Optional[Permission]:
        """
        Obtiene un permiso por su ID.
        
        Args:
            permission_id: ID del permiso.
            
        Returns:
            Optional[Permission]: Permiso encontrado o None.
        """
        pass
    
    @abstractmethod
    async def list_permissions(self, resource: Optional[str] = None) -> List[Permission]:
        """
        Lista los permisos disponibles, opcionalmente filtrados por recurso.
        
        Args:
            resource: Recurso para filtrar (opcional).
            
        Returns:
            List[Permission]: Lista de permisos.
        """
        pass
    
    @abstractmethod
    async def create_role(self, role: Role) -> Role:
        """
        Crea un nuevo rol en el sistema.
        
        Args:
            role: Rol a crear.
            
        Returns:
            Role: Rol creado con ID asignado.
        """
        pass
    
    @abstractmethod
    async def get_role(self, role_id: str) -> Optional[Role]:
        """
        Obtiene un rol por su ID.
        
        Args:
            role_id: ID del rol.
            
        Returns:
            Optional[Role]: Rol encontrado o None.
        """
        pass
    
    @abstractmethod
    async def list_roles(self) -> List[Role]:
        """
        Lista todos los roles disponibles.
        
        Returns:
            List[Role]: Lista de roles.
        """
        pass
    
    @abstractmethod
    async def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        """
        Asigna un rol a un usuario.
        
        Args:
            user_id: ID del usuario.
            role_id: ID del rol.
            
        Returns:
            bool: True si se asignó correctamente.
        """
        pass
    
    @abstractmethod
    async def get_user_roles(self, user_id: str) -> List[Role]:
        """
        Obtiene los roles asignados a un usuario.
        
        Args:
            user_id: ID del usuario.
            
        Returns:
            List[Role]: Lista de roles del usuario.
        """
        pass
    
    @abstractmethod
    async def check_permission(self, user_id: str, permission: Union[str, Permission]) -> bool:
        """
        Verifica si un usuario tiene un permiso específico.
        
        Args:
            user_id: ID del usuario.
            permission: Permiso a verificar.
            
        Returns:
            bool: True si el usuario tiene el permiso.
        """
        pass
