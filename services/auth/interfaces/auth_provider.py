"""
Interfaces abstractas para proveedores de autenticación.

Este módulo define las interfaces base que todos los adaptadores de autenticación
deben implementar, independientemente del mecanismo específico (JWT, OAuth, etc).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class UserIdentity:
    """
    Representación estándar de un usuario autenticado.
    Independiente del mecanismo de autenticación.
    """
    
    def __init__(
        self,
        id: str,
        username: Optional[str] = None,
        email: Optional[str] = None,
        roles: Optional[list] = None,
        permissions: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_authenticated: bool = False,
        expires_at: Optional[datetime] = None
    ):
        self.id = id
        self.username = username
        self.email = email
        self.roles = roles or []
        self.permissions = permissions or []
        self.metadata = metadata or {}
        self.is_authenticated = is_authenticated
        self.expires_at = expires_at
    
    @property
    def is_valid(self) -> bool:
        """Verifica si la identidad es válida y no ha expirado."""
        if not self.is_authenticated:
            return False
        
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
            
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la identidad a un diccionario."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "roles": self.roles,
            "permissions": self.permissions,
            "metadata": self.metadata,
            "is_authenticated": self.is_authenticated,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserIdentity':
        """Crea una instancia desde un diccionario."""
        expires_at = None
        if data.get("expires_at"):
            try:
                expires_at = datetime.fromisoformat(data["expires_at"])
            except (ValueError, TypeError):
                pass
                
        return cls(
            id=data.get("id", ""),
            username=data.get("username"),
            email=data.get("email"),
            roles=data.get("roles", []),
            permissions=data.get("permissions", []),
            metadata=data.get("metadata", {}),
            is_authenticated=data.get("is_authenticated", False),
            expires_at=expires_at
        )


class AuthProvider(ABC):
    """
    Interfaz abstracta para proveedores de autenticación.
    
    Esta clase define el contrato que todos los proveedores de autenticación deben
    implementar (JWT, OAuth, API Keys, etc).
    """
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Inicializa el proveedor con la configuración proporcionada.
        
        Args:
            config: Configuración específica del proveedor (secretos, URLs, etc).
            
        Returns:
            bool: True si la inicialización fue exitosa, False en caso contrario.
        """
        pass
        
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> UserIdentity:
        """
        Autentica un usuario con las credenciales proporcionadas.
        
        Args:
            credentials: Credenciales de autenticación (varía según el proveedor).
            
        Returns:
            UserIdentity: Información del usuario autenticado.
        """
        pass
        
    @abstractmethod
    async def validate_token(self, token: str) -> UserIdentity:
        """
        Valida un token de autenticación y retorna la identidad del usuario.
        
        Args:
            token: Token de autenticación a validar.
            
        Returns:
            UserIdentity: Información del usuario asociado al token.
        """
        pass
        
    @abstractmethod
    async def generate_token(self, user_id: str, **kwargs) -> str:
        """
        Genera un token de autenticación para un usuario.
        
        Args:
            user_id: ID del usuario.
            **kwargs: Datos adicionales a incluir en el token.
            
        Returns:
            str: Token generado.
        """
        pass
        
    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Refresca un token de autenticación.
        
        Args:
            refresh_token: Token de refresco.
            
        Returns:
            Dict[str, str]: Nuevo token de acceso y de refresco.
        """
        pass
        
    @abstractmethod
    async def revoke_token(self, token: str) -> bool:
        """
        Revoca un token de autenticación.
        
        Args:
            token: Token a revocar.
            
        Returns:
            bool: True si se revocó exitosamente, False en caso contrario.
        """
        pass
