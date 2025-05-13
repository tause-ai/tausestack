"""
Helpers para testing de autenticación en TauseStack.

Proporciona utilidades para probar fácilmente componentes de autenticación,
incluyendo generación de tokens, identidades simuladas y verificación de permisos.
"""

import time
import jwt
import uuid
import asyncio
from typing import Dict, Any, List, Optional, Set, Union
import pytest
from pydantic import BaseModel

from services.auth.interfaces.auth_provider import AuthProvider, UserIdentity, Permission, Role

class TestUserConfig(BaseModel):
    """Configuración para usuarios de prueba."""
    id: str = None
    email: str = "test@example.com"
    is_authenticated: bool = True
    is_anonymous: bool = False
    permissions: List[str] = []
    roles: List[str] = []
    metadata: Dict[str, Any] = {}
    
    def __init__(self, **data):
        """Inicializa con ID único si no se proporciona."""
        if "id" not in data or data["id"] is None:
            data["id"] = str(uuid.uuid4())
        super().__init__(**data)

class TestAuthProvider(AuthProvider):
    """
    Proveedor de autenticación para testing.
    
    Implementa AuthProvider pero permite controlar exactamente qué
    identidades y tokens se generan para facilitar las pruebas.
    """
    
    def __init__(self):
        """Inicializa el proveedor de testing."""
        self.users: Dict[str, UserIdentity] = {}
        self.tokens: Dict[str, str] = {}
        self.token_secret = "test-secret-key"
        self._initialized = False
    
    async def initialize(self, config: Dict[str, Any] = None) -> None:
        """
        Inicializa el proveedor con configuración opcional.
        
        Args:
            config: Configuración opcional.
        """
        self._initialized = True
        if config and "token_secret" in config:
            self.token_secret = config["token_secret"]
    
    async def authenticate(self, credentials: Dict[str, Any]) -> UserIdentity:
        """
        Autentica con credenciales de prueba.
        
        Args:
            credentials: Credenciales para autenticar.
            
        Returns:
            UserIdentity: Identidad del usuario.
        """
        self._ensure_initialized()
        
        # Verificar si hay un usuario asociado al email
        email = credentials.get("email", "")
        
        for user in self.users.values():
            if getattr(user, "email", "") == email:
                return user
        
        # No encontrado, devolver no autenticado
        return UserIdentity(id="", is_authenticated=False, is_anonymous=True)
    
    async def validate_token(self, token: str) -> UserIdentity:
        """
        Valida un token de prueba.
        
        Args:
            token: Token a validar.
            
        Returns:
            UserIdentity: Identidad del usuario.
        """
        self._ensure_initialized()
        
        # Verificar si es un token conocido
        if token in self.tokens:
            user_id = self.tokens[token]
            if user_id in self.users:
                return self.users[user_id]
        
        # Intentar decodificar jwt
        try:
            payload = jwt.decode(token, self.token_secret, algorithms=["HS256"])
            user_id = payload.get("sub", "")
            if user_id in self.users:
                return self.users[user_id]
        except:
            pass
        
        # Token inválido
        return UserIdentity(id="", is_authenticated=False, is_anonymous=True)
    
    async def create_token(self, user_id: str, expires_in: int = 3600) -> str:
        """
        Crea un token para un usuario.
        
        Args:
            user_id: ID del usuario.
            expires_in: Segundos hasta expiración.
            
        Returns:
            str: Token generado.
        """
        self._ensure_initialized()
        
        if user_id not in self.users:
            raise ValueError(f"Usuario con ID {user_id} no encontrado")
        
        # Crear token JWT
        now = int(time.time())
        payload = {
            "sub": user_id,
            "exp": now + expires_in,
            "iat": now,
            "nbf": now,
            "email": getattr(self.users[user_id], "email", "")
        }
        
        token = jwt.encode(payload, self.token_secret, algorithm="HS256")
        
        # Registrar token
        self.tokens[token] = user_id
        
        return token
    
    async def validate_permission(self, identity: UserIdentity, required_permission: Permission) -> bool:
        """
        Valida si un usuario tiene un permiso.
        
        Args:
            identity: Identidad del usuario.
            required_permission: Permiso requerido.
            
        Returns:
            bool: True si tiene permiso, False en caso contrario.
        """
        if not identity.is_authenticated:
            return False
        
        permissions = getattr(identity, "permissions", [])
        
        return str(required_permission) in permissions
    
    async def validate_role(self, identity: UserIdentity, required_role: Role) -> bool:
        """
        Valida si un usuario tiene un rol.
        
        Args:
            identity: Identidad del usuario.
            required_role: Rol requerido.
            
        Returns:
            bool: True si tiene el rol, False en caso contrario.
        """
        if not identity.is_authenticated:
            return False
        
        roles = getattr(identity, "roles", [])
        
        return str(required_role) in roles
    
    def _ensure_initialized(self) -> None:
        """Verifica que el proveedor esté inicializado."""
        if not self._initialized:
            raise RuntimeError("El proveedor de autenticación no está inicializado")
    
    # Métodos específicos para testing
    
    def add_test_user(self, user_config: TestUserConfig) -> UserIdentity:
        """
        Añade un usuario de prueba.
        
        Args:
            user_config: Configuración del usuario.
            
        Returns:
            UserIdentity: Identidad creada.
        """
        # Crear identidad de usuario
        identity = UserIdentity(id=user_config.id, is_authenticated=user_config.is_authenticated)
        
        # Añadir propiedades adicionales
        identity.email = user_config.email
        identity.is_anonymous = user_config.is_anonymous
        identity.permissions = user_config.permissions
        identity.roles = user_config.roles
        
        # Añadir metadatos
        for key, value in user_config.metadata.items():
            setattr(identity, key, value)
        
        # Registrar usuario
        self.users[user_config.id] = identity
        
        return identity
    
    def remove_test_user(self, user_id: str) -> None:
        """
        Elimina un usuario de prueba.
        
        Args:
            user_id: ID del usuario a eliminar.
        """
        if user_id in self.users:
            del self.users[user_id]
            
            # Eliminar tokens asociados
            self.tokens = {k: v for k, v in self.tokens.items() if v != user_id}
    
    def clear_all(self) -> None:
        """Limpia todos los usuarios y tokens de prueba."""
        self.users = {}
        self.tokens = {}

# Fixtures para pytest

@pytest.fixture
def test_auth_provider():
    """
    Fixture que proporciona un proveedor de autenticación para pruebas.
    
    Returns:
        TestAuthProvider: Proveedor de autenticación para pruebas.
    """
    provider = TestAuthProvider()
    asyncio.run(provider.initialize())
    yield provider
    provider.clear_all()

@pytest.fixture
def test_user(test_auth_provider):
    """
    Fixture que proporciona un usuario de prueba.
    
    Args:
        test_auth_provider: Proveedor de autenticación (inyectado por pytest).
        
    Returns:
        Dict[str, Any]: Datos del usuario.
    """
    # Crear configuración de usuario
    user_config = TestUserConfig(
        email="user@example.com",
        permissions=["read:content", "write:content"],
        roles=["user"]
    )
    
    # Añadir al proveedor
    identity = test_auth_provider.add_test_user(user_config)
    
    # Generar token
    token = asyncio.run(test_auth_provider.create_token(identity.id))
    
    return {
        "id": identity.id,
        "email": identity.email,
        "token": token,
        "identity": identity
    }

@pytest.fixture
def test_admin(test_auth_provider):
    """
    Fixture que proporciona un usuario administrador de prueba.
    
    Args:
        test_auth_provider: Proveedor de autenticación (inyectado por pytest).
        
    Returns:
        Dict[str, Any]: Datos del administrador.
    """
    # Crear configuración de admin
    admin_config = TestUserConfig(
        email="admin@example.com",
        permissions=["read:content", "write:content", "admin:all"],
        roles=["user", "admin"]
    )
    
    # Añadir al proveedor
    identity = test_auth_provider.add_test_user(admin_config)
    
    # Generar token
    token = asyncio.run(test_auth_provider.create_token(identity.id))
    
    return {
        "id": identity.id,
        "email": identity.email,
        "token": token,
        "identity": identity
    }

# Ejemplo de uso en un test
"""
import pytest
from services.testing.helpers.auth_test_helpers import test_auth_provider, test_user, test_admin

def test_validar_permiso(test_auth_provider, test_user):
    # Verificar que el usuario tiene un permiso específico
    identity = test_user["identity"]
    result = asyncio.run(test_auth_provider.validate_permission(identity, "read:content"))
    assert result is True
    
    # Verificar que no tiene otro permiso
    result = asyncio.run(test_auth_provider.validate_permission(identity, "admin:all"))
    assert result is False

def test_validar_token(test_auth_provider, test_admin):
    # Verificar que el token del admin es válido
    token = test_admin["token"]
    identity = asyncio.run(test_auth_provider.validate_token(token))
    assert identity.is_authenticated
    assert identity.id == test_admin["id"]
    assert "admin" in identity.roles
"""
