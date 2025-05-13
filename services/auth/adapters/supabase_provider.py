"""
Adaptador de autenticación Supabase para Tausestack.

Este módulo implementa la interfaz AuthProvider utilizando Supabase
como proveedor de autenticación, integrando todas sus funcionalidades
de inicio de sesión, validación de tokens y gestión de sesiones.
"""

import json
import httpx
import jwt
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from supabase import create_client, Client
from gotrue import AuthResponse, UserResponse, Session

from ..interfaces.auth_provider import AuthProvider, UserIdentity

class SupabaseAuthProvider(AuthProvider):
    """
    Implementación de AuthProvider que utiliza Supabase Auth.
    
    Esta clase proporciona autenticación basada en Supabase, aprovechando
    sus capacidades de autenticación multifactor, proveedores OAuth y
    gestión de sesiones.
    """
    
    def __init__(self):
        self.supabase_url = None
        self.supabase_key = None
        self.client = None
        self.jwt_secret = None
        self.refresh_token_cookie_name = "sb-refresh-token"
        self.access_token_cookie_name = "sb-access-token"
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Inicializa el proveedor Supabase con la configuración proporcionada.
        
        Args:
            config: Configuración que incluye supabase_url, supabase_key, etc.
            
        Returns:
            bool: True si la inicialización fue exitosa.
        """
        try:
            self.supabase_url = config.get("supabase_url")
            self.supabase_key = config.get("supabase_key")
            
            if not self.supabase_url or not self.supabase_key:
                return False
            
            # Para validación local de tokens (opcional)
            self.jwt_secret = config.get("jwt_secret")
            
            # Crear cliente de Supabase
            self.client = create_client(self.supabase_url, self.supabase_key)
            
            # Configuración adicional
            self.refresh_token_cookie_name = config.get(
                "refresh_token_cookie_name", 
                self.refresh_token_cookie_name
            )
            self.access_token_cookie_name = config.get(
                "access_token_cookie_name",
                self.access_token_cookie_name
            )
            
            return True
        except Exception:
            return False
    
    async def authenticate(self, credentials: Dict[str, Any]) -> UserIdentity:
        """
        Autentica un usuario con las credenciales proporcionadas.
        
        Soporta múltiples métodos de autenticación de Supabase:
        - Email/password
        - Magic link
        - OAuth providers
        - Phone
        
        Args:
            credentials: Incluye tipo de auth y credenciales específicas.
            
        Returns:
            UserIdentity: Identidad del usuario autenticado.
        """
        try:
            auth_type = credentials.get("auth_type", "password")
            
            if auth_type == "password":
                email = credentials.get("email")
                password = credentials.get("password")
                
                if not email or not password:
                    return UserIdentity(id="", is_authenticated=False)
                
                # Autenticar con email/password
                auth_response = self.client.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                
                return self._process_auth_response(auth_response)
                
            elif auth_type == "magic_link":
                email = credentials.get("email")
                
                if not email:
                    return UserIdentity(id="", is_authenticated=False)
                
                # Enviar magic link (no autentifica inmediatamente)
                self.client.auth.sign_in_with_otp({
                    "email": email
                })
                
                # En este caso, no podemos devolver una identidad autenticada
                # ya que el usuario debe hacer clic en el enlace enviado por email
                return UserIdentity(
                    id="pending",
                    email=email,
                    is_authenticated=False,
                    metadata={"auth_type": "magic_link", "status": "pending"}
                )
                
            elif auth_type == "oauth":
                # Esto normalmente se maneja en el frontend con redirección
                provider = credentials.get("provider")  # google, github, etc.
                
                # Devolvemos información para construir la URL de redirección
                return UserIdentity(
                    id="pending",
                    is_authenticated=False,
                    metadata={
                        "auth_type": "oauth",
                        "provider": provider,
                        "redirect_url": f"{self.supabase_url}/auth/v1/authorize?provider={provider}"
                    }
                )
                
            elif auth_type == "phone":
                phone = credentials.get("phone")
                
                if not phone:
                    return UserIdentity(id="", is_authenticated=False)
                
                # Enviar OTP al teléfono
                self.client.auth.sign_in_with_otp({
                    "phone": phone
                })
                
                return UserIdentity(
                    id="pending",
                    is_authenticated=False,
                    metadata={"auth_type": "phone", "status": "pending"}
                )
                
            else:
                return UserIdentity(id="", is_authenticated=False)
                
        except Exception as e:
            # En caso de error, devolver usuario no autenticado
            return UserIdentity(
                id="",
                is_authenticated=False,
                metadata={"error": str(e)}
            )
    
    async def validate_token(self, token: str) -> UserIdentity:
        """
        Valida un token JWT de Supabase y retorna la identidad del usuario.
        
        Args:
            token: Token JWT a validar.
            
        Returns:
            UserIdentity: Identidad del usuario si el token es válido.
        """
        try:
            # Establecer el token en el cliente para validación
            self.client.auth.set_session(token, None)
            
            # Obtener la sesión actual
            session = self.client.auth.get_session()
            
            if not session:
                return UserIdentity(id="", is_authenticated=False)
            
            # Extraer datos del usuario
            user = session.user
            
            if not user:
                return UserIdentity(id="", is_authenticated=False)
            
            # Convertir el timestamp de expiración a datetime
            expires_at = None
            if session.expires_at:
                expires_at = datetime.fromtimestamp(session.expires_at)
            
            # Extraer roles y permisos de los metadatos del usuario (App Metadata)
            app_metadata = user.app_metadata or {}
            roles = app_metadata.get("roles", [])
            permissions = []
            
            # En Supabase, los permisos suelen implementarse a nivel de RLS
            # Pero podemos extraerlos si se almacenan en los metadatos
            if "permissions" in app_metadata:
                permissions = app_metadata["permissions"]
            
            # Obtener metadatos personalizados
            user_metadata = user.user_metadata or {}
            
            return UserIdentity(
                id=user.id,
                email=user.email,
                username=user_metadata.get("username"),
                roles=roles,
                permissions=permissions,
                metadata=user_metadata,
                is_authenticated=True,
                expires_at=expires_at
            )
            
        except Exception:
            return UserIdentity(id="", is_authenticated=False)
    
    async def generate_token(self, user_id: str, **kwargs) -> str:
        """
        Este método no es aplicable directamente a Supabase, 
        ya que Supabase maneja sus propios tokens.
        
        En cambio, devolvemos un token de sesión existente o lanzamos una excepción.
        
        Args:
            user_id: ID del usuario.
            **kwargs: Datos adicionales.
            
        Returns:
            str: Token de sesión actual.
            
        Raises:
            ValueError: Si no hay sesión activa.
        """
        try:
            session = self.client.auth.get_session()
            if not session or not session.access_token:
                raise ValueError("No hay una sesión activa")
                
            return session.access_token
        except Exception as e:
            raise ValueError(f"No se pudo generar/obtener token: {str(e)}")
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Refresca un token de Supabase utilizando el refresh_token.
        
        Args:
            refresh_token: Token de refresco de Supabase.
            
        Returns:
            Dict[str, str]: Nuevo token de acceso y de refresco.
            
        Raises:
            ValueError: Si el refresco falla.
        """
        try:
            # Refrescar la sesión con el refresh token
            response = self.client.auth.refresh_session(refresh_token)
            
            if not response or not response.session:
                raise ValueError("Error al refrescar el token")
            
            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "token_type": "bearer"
            }
        except Exception as e:
            raise ValueError(f"Error al refrescar el token: {str(e)}")
    
    async def revoke_token(self, token: str) -> bool:
        """
        Cierra la sesión en Supabase, invalidando el token.
        
        Args:
            token: Token a revocar (en este caso, puede ser ignorado ya que
                 usamos la sesión actual del cliente).
            
        Returns:
            bool: True si se revocó correctamente.
        """
        try:
            # Establecer el token a revocar como sesión actual
            self.client.auth.set_session(token, None)
            
            # Cerrar sesión
            self.client.auth.sign_out()
            return True
        except Exception:
            return False
    
    def _process_auth_response(self, auth_response: AuthResponse) -> UserIdentity:
        """
        Procesa la respuesta de autenticación de Supabase.
        
        Args:
            auth_response: Respuesta de la autenticación.
            
        Returns:
            UserIdentity: Identidad del usuario autenticado.
        """
        if not auth_response or not auth_response.user:
            return UserIdentity(id="", is_authenticated=False)
        
        session = auth_response.session
        user = auth_response.user
        
        # Calcular fecha de expiración
        expires_at = None
        if session and session.expires_at:
            expires_at = datetime.fromtimestamp(session.expires_at)
        
        # Extraer roles y permisos
        app_metadata = user.app_metadata or {}
        user_metadata = user.user_metadata or {}
        roles = app_metadata.get("roles", [])
        permissions = app_metadata.get("permissions", [])
        
        return UserIdentity(
            id=user.id,
            email=user.email,
            username=user_metadata.get("username"),
            roles=roles,
            permissions=permissions,
            metadata={
                "user_metadata": user_metadata,
                "app_metadata": app_metadata
            },
            is_authenticated=True,
            expires_at=expires_at
        )
