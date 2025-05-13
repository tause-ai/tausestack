"""
Adaptador de autenticación JWT para Tausestack.

Este módulo implementa la interfaz AuthProvider utilizando JSON Web Tokens (JWT)
como mecanismo de autenticación, incluyendo generación, validación y gestión de tokens.
"""

import jwt
import time
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..interfaces.auth_provider import AuthProvider, UserIdentity

class JWTAuthProvider(AuthProvider):
    """
    Implementación de AuthProvider que utiliza JSON Web Tokens (JWT).
    
    Esta clase proporciona autenticación basada en JWT, generando tokens
    con expiración, datos de usuario y claims personalizados.
    """
    
    def __init__(self):
        self.secret_key = None
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        self.issuer = "tausestack"
        self.audience = None
        self.blacklisted_tokens = set()  # En producción, usar una DB/Redis
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Inicializa el proveedor JWT con la configuración proporcionada.
        
        Args:
            config: Configuración que incluye secret_key, algoritmo, etc.
            
        Returns:
            bool: True si la inicialización fue exitosa.
        """
        try:
            self.secret_key = config.get("secret_key")
            if not self.secret_key:
                return False
                
            # Configuración opcional
            self.algorithm = config.get("algorithm", self.algorithm)
            self.access_token_expire_minutes = config.get(
                "access_token_expire_minutes", 
                self.access_token_expire_minutes
            )
            self.refresh_token_expire_days = config.get(
                "refresh_token_expire_days",
                self.refresh_token_expire_days
            )
            self.issuer = config.get("issuer", self.issuer)
            self.audience = config.get("audience", self.audience)
            
            return True
        except Exception:
            return False
    
    async def authenticate(self, credentials: Dict[str, Any]) -> UserIdentity:
        """
        Autentica un usuario con las credenciales proporcionadas.
        
        Esta implementación espera que las credenciales ya estén verificadas previamente,
        y solo genera un token JWT con los datos del usuario.
        
        Args:
            credentials: Debe incluir "user_id" y opcionalmente otros datos.
            
        Returns:
            UserIdentity: Identidad del usuario autenticado.
        """
        if "user_id" not in credentials:
            return UserIdentity(id="", is_authenticated=False)
            
        user_id = credentials["user_id"]
        username = credentials.get("username")
        email = credentials.get("email")
        roles = credentials.get("roles", [])
        permissions = credentials.get("permissions", [])
        metadata = credentials.get("metadata", {})
        
        # Calcular expiración
        expires_at = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        return UserIdentity(
            id=user_id,
            username=username,
            email=email,
            roles=roles,
            permissions=permissions,
            metadata=metadata,
            is_authenticated=True,
            expires_at=expires_at
        )
    
    async def validate_token(self, token: str) -> UserIdentity:
        """
        Valida un token JWT y retorna la identidad del usuario.
        
        Args:
            token: Token JWT a validar.
            
        Returns:
            UserIdentity: Identidad del usuario si el token es válido.
        """
        if not token or token in self.blacklisted_tokens:
            return UserIdentity(id="", is_authenticated=False)
            
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_signature": True}
            )
            
            # Extraer datos del usuario del payload
            user_id = payload.get("sub", "")
            exp = payload.get("exp")
            expires_at = datetime.fromtimestamp(exp) if exp else None
            
            return UserIdentity(
                id=user_id,
                username=payload.get("username"),
                email=payload.get("email"),
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
                metadata=payload.get("metadata", {}),
                is_authenticated=True,
                expires_at=expires_at
            )
        except jwt.PyJWTError:
            return UserIdentity(id="", is_authenticated=False)
    
    async def generate_token(self, user_id: str, **kwargs) -> str:
        """
        Genera un token JWT para un usuario.
        
        Args:
            user_id: ID del usuario.
            **kwargs: Datos adicionales a incluir en el token.
            
        Returns:
            str: Token JWT generado.
        """
        # Tiempo de expiración
        expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        expire = datetime.utcnow() + expires_delta
        
        # Preparar payload
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())
        }
        
        if self.issuer:
            payload["iss"] = self.issuer
            
        if self.audience:
            payload["aud"] = self.audience
        
        # Añadir datos adicionales
        for key, value in kwargs.items():
            if key not in payload:
                payload[key] = value
        
        # Generar token
        token = jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm
        )
        
        return token
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Refresca un token JWT generando uno nuevo.
        
        Args:
            refresh_token: Token de refresco a validar.
            
        Returns:
            Dict[str, str]: Nuevo token de acceso y de refresco.
        """
        # Validar refresh token
        identity = await self.validate_token(refresh_token)
        if not identity.is_authenticated:
            raise ValueError("Token de refresco inválido o expirado")
        
        # Revocar el token anterior
        await self.revoke_token(refresh_token)
        
        # Generar nuevo access token
        access_token = await self.generate_token(
            identity.id,
            username=identity.username,
            email=identity.email,
            roles=identity.roles,
            permissions=identity.permissions,
            metadata=identity.metadata
        )
        
        # Generar nuevo refresh token (con mayor duración)
        refresh_expires = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        new_refresh_token = jwt.encode(
            {
                "sub": identity.id,
                "exp": refresh_expires,
                "iat": datetime.utcnow(),
                "jti": str(uuid.uuid4()),
                "type": "refresh"
            },
            self.secret_key,
            algorithm=self.algorithm
        )
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    
    async def revoke_token(self, token: str) -> bool:
        """
        Revoca un token JWT agregándolo a una lista negra.
        
        En producción, se debería usar una base de datos o Redis.
        
        Args:
            token: Token a revocar.
            
        Returns:
            bool: True si se revocó correctamente.
        """
        try:
            # En producción: guardar en base de datos o Redis
            self.blacklisted_tokens.add(token)
            return True
        except Exception:
            return False
