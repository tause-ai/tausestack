import pytest
import os
from services.storage import SupabaseStorageProvider

@pytest.mark.asyncio
class TestSupabaseStorageProvider:
    """
    Tests de integración para SupabaseStorageProvider.
    Requiere variables de entorno SUPABASE_URL, SUPABASE_KEY y bucket de pruebas.
    """
    @pytest.fixture(scope="class")
    def storage(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        bucket = os.getenv("SUPABASE_BUCKET", "public")
        if not url or not key:
            pytest.skip("No hay configuración de Supabase Storage para pruebas.")
        return SupabaseStorageProvider(supabase_url=url, supabase_key=key, bucket=bucket)

    @pytest.mark.asyncio
    async def test_save_and_load(self, storage):
        content = b"hola mundo desde test"
        path = "test/test_file.txt"
        storage.save(path, content)
        loaded = storage.load(path)
        assert loaded == content

    @pytest.mark.asyncio
    async def test_list_and_delete(self, storage):
        path = "test/test_list_delete.txt"
        storage.save(path, b"data para listar y borrar")
        archivos = storage.list("test/")
        assert path.split("/", 1)[-1] in archivos or path in archivos
        storage.delete(path)
        # Debe lanzar FileNotFoundError al intentar cargar
        with pytest.raises(Exception):
            storage.load(path)
