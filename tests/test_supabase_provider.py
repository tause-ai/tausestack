import pytest
import os
from services.auth.adapters.supabase_provider import SupabaseAuthProvider

@pytest.mark.asyncio
class TestSupabaseAuthProvider:
    """
    Tests básicos para SupabaseAuthProvider.
    NOTA: Estos tests requieren variables de entorno reales de Supabase para pruebas de integración.
    Si no están presentes, los tests se omiten automáticamente.
    """
    
    @pytest.fixture(scope="class")
    def supabase_config(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            pytest.skip("No hay variables de entorno SUPABASE_URL y SUPABASE_KEY para pruebas reales.")
        return {"supabase_url": url, "supabase_key": key}

    @pytest.mark.asyncio
    async def test_initialize_ok(self, supabase_config):
        provider = SupabaseAuthProvider()
        result = await provider.initialize(supabase_config)
        assert result is True
        assert provider.client is not None

    @pytest.mark.asyncio
    async def test_initialize_fail(self):
        provider = SupabaseAuthProvider()
        with pytest.raises(ValueError):
            await provider.initialize({"supabase_url": "", "supabase_key": ""})

    @pytest.mark.asyncio
    async def test_authenticate_password(self, supabase_config):
        """
        Test de autenticación por email/password con Supabase.
        Requiere usuario de pruebas válido en tu proyecto Supabase.
        """
        provider = SupabaseAuthProvider()
        await provider.initialize(supabase_config)
        email = os.getenv("SUPABASE_TEST_EMAIL")
        password = os.getenv("SUPABASE_TEST_PASSWORD")
        if not email or not password:
            pytest.skip("No hay credenciales de prueba SUPABASE_TEST_EMAIL/SUPABASE_TEST_PASSWORD.")
        identity = await provider.authenticate({
            "auth_type": "password",
            "email": email,
            "password": password
        })
        assert identity.is_authenticated
        assert identity.email == email

    @pytest.mark.asyncio
    async def test_authenticate_magic_link(self, supabase_config):
        """
        Test de autenticación por magic link (flujo simulado).
        Solo verifica que el método no falla y retorna un UserIdentity pendiente.
        """
        provider = SupabaseAuthProvider()
        await provider.initialize(supabase_config)
        email = os.getenv("SUPABASE_TEST_EMAIL")
        if not email:
            pytest.skip("No hay correo de prueba SUPABASE_TEST_EMAIL.")
        identity = await provider.authenticate({
            "auth_type": "magic_link",
            "email": email
        })
        assert identity.is_authenticated is False
        assert identity.metadata.get("auth_type") == "magic_link"

    @pytest.mark.asyncio
    async def test_refresh_token(self, supabase_config):
        """
        Test de refresh de token: autentica, obtiene refresh_token y solicita nuevos tokens.
        """
        provider = SupabaseAuthProvider()
        await provider.initialize(supabase_config)
        email = os.getenv("SUPABASE_TEST_EMAIL")
        password = os.getenv("SUPABASE_TEST_PASSWORD")
        if not email or not password:
            pytest.skip("No hay credenciales de prueba SUPABASE_TEST_EMAIL/SUPABASE_TEST_PASSWORD.")
        identity = await provider.authenticate({
            "auth_type": "password",
            "email": email,
            "password": password
        })
        if not identity.is_authenticated or not hasattr(identity, "metadata") or "refresh_token" not in identity.metadata:
            pytest.skip("No se obtuvo refresh_token tras autenticación. Revisa el usuario de pruebas.")
        refresh_token = identity.metadata["refresh_token"]
        tokens = await provider.refresh_token(refresh_token)
        assert "access_token" in tokens
        assert "refresh_token" in tokens

    @pytest.mark.asyncio
    async def test_revoke_token(self, supabase_config):
        """
        Test de revocación de token: autentica, revoca el access_token y verifica que no es válido.
        """
        provider = SupabaseAuthProvider()
        await provider.initialize(supabase_config)
        email = os.getenv("SUPABASE_TEST_EMAIL")
        password = os.getenv("SUPABASE_TEST_PASSWORD")
        if not email or not password:
            pytest.skip("No hay credenciales de prueba SUPABASE_TEST_EMAIL/SUPABASE_TEST_PASSWORD.")
        identity = await provider.authenticate({
            "auth_type": "password",
            "email": email,
            "password": password
        })
        if not identity.is_authenticated or not hasattr(identity, "metadata") or "access_token" not in identity.metadata:
            pytest.skip("No se obtuvo access_token tras autenticación. Revisa el usuario de pruebas.")
        token = identity.metadata["access_token"]
        # Revocar el token
        revoked = await provider.revoke_token(token)
        assert revoked is True
        # Intentar validar el token revocado
        validated = await provider.validate_token(token)
        assert validated.is_authenticated is False
        assert validated.email is None or validated.email == ""

    @pytest.mark.asyncio
    async def test_validate_token(self, supabase_config):
        """
        Test de validación de token: genera un token válido y lo valida.
        """
        provider = SupabaseAuthProvider()
        await provider.initialize(supabase_config)
        email = os.getenv("SUPABASE_TEST_EMAIL")
        password = os.getenv("SUPABASE_TEST_PASSWORD")
        if not email or not password:
            pytest.skip("No hay credenciales de prueba SUPABASE_TEST_EMAIL/SUPABASE_TEST_PASSWORD.")
        identity = await provider.authenticate({
            "auth_type": "password",
            "email": email,
            "password": password
        })
        if not identity.is_authenticated or not hasattr(identity, "metadata") or "access_token" not in identity.metadata:
            pytest.skip("No se obtuvo access_token tras autenticación. Revisa el usuario de pruebas.")
        token = identity.metadata["access_token"]
        validated = await provider.validate_token(token)
        assert validated.is_authenticated
        assert validated.email == email
