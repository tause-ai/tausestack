# Tests for LocalJsonStorage backend
import pytest
import os
import shutil
import json
from pathlib import Path

from tausestack.sdk.storage.backends import LocalJsonStorage

# Directorio base temporal para las pruebas de almacenamiento
TEST_BASE_STORAGE_PATH = Path("./.tmp_test_storage")

@pytest.fixture
def tmp_storage_path(request):
    """
    Crea un directorio de almacenamiento temporal para una prueba
    y lo limpia después.
    """
    test_specific_path = TEST_BASE_STORAGE_PATH / request.node.name
    if test_specific_path.exists():
        shutil.rmtree(test_specific_path)
    test_specific_path.mkdir(parents=True, exist_ok=True)
    
    yield test_specific_path
    
    if test_specific_path.exists():
        shutil.rmtree(test_specific_path)

@pytest.fixture
def local_storage(tmp_storage_path):
    """
    Proporciona una instancia de LocalJsonStorage usando el path temporal.
    """
    return LocalJsonStorage(base_path=str(tmp_storage_path))

def test_put_and_get_json(local_storage: LocalJsonStorage, tmp_storage_path: Path):
    """
    Verifica que se puede guardar un diccionario y luego recuperarlo correctamente.
    """
    key = "test_data_01.json"
    data_to_store = {"name": "Tause", "version": "1.0", "active": True}
    
    local_storage.put(key, data_to_store)
    
    expected_file_path = tmp_storage_path / key
    assert expected_file_path.exists()
    assert expected_file_path.is_file()
    
    with open(expected_file_path, 'r') as f:
        content_on_disk = json.load(f)
    assert content_on_disk == data_to_store
    
    retrieved_data = local_storage.get(key)
    assert retrieved_data is not None
    assert retrieved_data == data_to_store

def test_get_non_existent_json(local_storage: LocalJsonStorage):
    """
    Verifica que al intentar obtener una clave que no existe, se devuelve None.
    """
    key = "non_existent_key.json"
    retrieved_data = local_storage.get(key)
    assert retrieved_data is None

def test_delete_json(local_storage: LocalJsonStorage, tmp_storage_path: Path):
    """
    Verifica que después de eliminar una clave, get devuelve None
    y el archivo se elimina físicamente.
    """
    key = "to_be_deleted.json"
    data_to_store = {"message": "delete me"}
    
    local_storage.put(key, data_to_store)
    expected_file_path = tmp_storage_path / key
    assert expected_file_path.exists()
    
    local_storage.delete(key)
    
    assert local_storage.get(key) is None
    assert not expected_file_path.exists()

def test_put_creates_directory_structure(tmp_storage_path: Path):
    """
    Verifica que el método put crea la estructura de directorios necesaria
    si no existe, incluyendo subdirectorios en la clave.
    """
    key_with_subdir = "subdir1/subdir2/test_data_02.json"
    data_to_store = {"info": "nested structure"}
    
    storage = LocalJsonStorage(base_path=str(tmp_storage_path))
    storage.put(key_with_subdir, data_to_store)
    
    expected_file_path = tmp_storage_path / key_with_subdir
    assert expected_file_path.exists()
    assert expected_file_path.is_file()
    
    with open(expected_file_path, 'r') as f:
        content_on_disk = json.load(f)
    assert content_on_disk == data_to_store

def test_delete_non_existent_json(local_storage: LocalJsonStorage):
    """
    Verifica que intentar eliminar una clave que no existe no produce un error.
    """
    key = "non_existent_for_delete.json"
    try:
        local_storage.delete(key)
    except Exception as e:
        pytest.fail(f"Deleting non-existent key raised an exception: {e}")

def test_overwrite_existing_json(local_storage: LocalJsonStorage, tmp_storage_path: Path):
    """
    Verifica que put sobrescribe correctamente un archivo JSON existente.
    """
    key = "overwrite_me.json"
    initial_data = {"status": "initial"}
    updated_data = {"status": "updated", "new_field": True}
    
    local_storage.put(key, initial_data)
    retrieved_initial = local_storage.get(key)
    assert retrieved_initial == initial_data
    
    local_storage.put(key, updated_data)
    
    retrieved_updated = local_storage.get(key)
    assert retrieved_updated == updated_data
    
    expected_file_path = tmp_storage_path / key
    with open(expected_file_path, 'r') as f:
        content_on_disk = json.load(f)
    assert content_on_disk == updated_data
