import pytest
from fastapi import HTTPException
from unittest.mock import patch, MagicMock
from services.users.core.auth import decode_access_token, auth_provider

# Pruebas para la función decode_access_token
class TestAuthDecodeToken:
    @pytest.mark.asyncio
    async def test_decode_valid_token(self):
        # Configurar mock para token válido
        mock_claims = {
            "sub": "user-123",
            "email": "test@example.com",
            "user_metadata": {"name": "Test User"},
            "app_metadata": {"roles": ["user"]}
        }
        
        with patch.object(auth_provider, 'validate_token', return_value=mock_claims):
            result = decode_access_token("valid.token.here")
            assert result == mock_claims
    
    @pytest.mark.asyncio
    async def test_decode_invalid_token_returns_none(self):
        with patch.object(auth_provider, 'validate_token', side_effect=Exception("Invalid token")):
            result = decode_access_token("invalid.token.here")
            assert result is None

# Pruebas para la integración con Supabase Auth
class TestSupabaseIntegration:
    @pytest.mark.asyncio
    async def test_auth_provider_requires_config(self):
        # Probar que el proveedor requiere configuración
        with pytest.raises(ValueError):
            from services.auth.adapters.supabase_provider import SupabaseAuthProvider
            SupabaseAuthProvider({})
    
    @pytest.mark.asyncio
    async def test_validate_token_with_mock(self, mock_supabase_auth):
        # Configurar mock para Supabase
        mock_supabase_auth.get_user.return_value = {
            "user": {"id": "test-id"},
            "session": {}
        }
        
        # Inyectar mock en el auth_provider
        with patch('services.users.core.auth.auth_provider.client.auth', mock_supabase_auth):
            claims = auth_provider.validate_token("test-token")
            assert claims["sub"] == "test-id"

# Pruebas de seguridad
class TestSecurity:
    @pytest.mark.asyncio
    async def test_no_hardcoded_secrets(self):
        # Asegurar que no hay claves hardcodeadas en el código
        with open("services/users/core/auth.py") as f:
            content = f.read()
            assert "SECRET_KEY" not in content
            assert "super-secret" not in content
