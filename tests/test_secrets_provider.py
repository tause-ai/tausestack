import pytest
import os
from services.secrets import EnvSecretsProvider, SupabaseSecretsProvider

class TestEnvSecretsProvider:
    def test_get_existing_env(self, monkeypatch):
        monkeypatch.setenv("TEST_SECRET", "valor123")
        provider = EnvSecretsProvider()
        assert provider.get("TEST_SECRET") == "valor123"

    def test_get_missing_env_with_default(self, monkeypatch):
        monkeypatch.delenv("TEST_SECRET", raising=False)
        provider = EnvSecretsProvider()
        assert provider.get("TEST_SECRET", default="defecto") == "defecto"

@pytest.mark.asyncio
def test_supabase_secrets_provider(monkeypatch):
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        pytest.skip("No hay configuración de Supabase para pruebas.")
    # Debe existir una tabla 'secrets' y un registro con key='TEST_SECRET' y value='valor_supabase'
    provider = SupabaseSecretsProvider(supabase_url=url, supabase_key=key, fallback_env=False)
    valor = provider.get("TEST_SECRET")
    assert valor == "valor_supabase"

@pytest.mark.asyncio
def test_supabase_secrets_provider_fallback(monkeypatch):
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        pytest.skip("No hay configuración de Supabase para pruebas.")
    monkeypatch.setenv("TEST_SECRET", "valor_env_fallback")
    # Si no existe en Supabase, debe retornar el de entorno
    provider = SupabaseSecretsProvider(supabase_url=url, supabase_key=key, fallback_env=True)
    valor = provider.get("NO_EXISTE_EN_SUPABASE")
    assert valor == "valor_env_fallback"
