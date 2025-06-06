import os
import tempfile
import pytest
from services.storage.provider import LocalStorageProvider

CHUNK_SIZE = 1024 * 1024  # 1MB

def generate_large_data(size_mb):
    return os.urandom(size_mb * 1024 * 1024)

def test_save_and_load_chunks():
    provider = LocalStorageProvider(base_dir=tempfile.mkdtemp())
    path = "testfile.bin"
    data = generate_large_data(5)  # 5MB
    # Guardar archivo completo
    provider.save(path, data)
    num_chunks = provider.get_num_chunks(path, CHUNK_SIZE)
    # Guardar cada chunk como archivo separado
    for i in range(num_chunks):
        start = i * CHUNK_SIZE
        end = min((i+1) * CHUNK_SIZE, len(data))
        chunk = data[start:end]
        provider.save_chunk(path, chunk, i)
    # Leer y reconstruir desde chunks
    reconstructed = b''
    for i in range(num_chunks):
        chunk = provider.load_chunk(path, i, CHUNK_SIZE)
        reconstructed += chunk
    assert reconstructed == data

def test_invalid_key_regex():
    provider = LocalStorageProvider(base_dir=tempfile.mkdtemp())
    invalid_keys = [
        "inva|id.txt", "bad*name.bin", "white space.txt", "ç.txt", "a/bad\\path.txt"
    ]
    for key in invalid_keys:
        with pytest.raises(ValueError):
            provider.save(key, b"data")
        with pytest.raises(ValueError):
            provider.load(key)
        with pytest.raises(ValueError):
            provider.delete(key)
        with pytest.raises(ValueError):
            provider.save_chunk(key, b"chunk", 0)
        with pytest.raises(ValueError):
            provider.load_chunk(key, 0, CHUNK_SIZE)
        with pytest.raises(ValueError):
            provider.get_num_chunks(key, CHUNK_SIZE)

def test_invalid_key_path_traversal():
    provider = LocalStorageProvider(base_dir=tempfile.mkdtemp())
    keys = ["../evil.txt", "/abs/path.txt", "folder/../../escape.txt"]
    for key in keys:
        with pytest.raises(ValueError):
            provider.save(key, b"data")
        with pytest.raises(ValueError):
            provider.load(key)
        with pytest.raises(ValueError):
            provider.delete(key)
        with pytest.raises(ValueError):
            provider.save_chunk(key, b"chunk", 0)
        with pytest.raises(ValueError):
            provider.load_chunk(key, 0, CHUNK_SIZE)
        with pytest.raises(ValueError):
            provider.get_num_chunks(key, CHUNK_SIZE)

def test_missing_chunk_raises():
    provider = LocalStorageProvider(base_dir=tempfile.mkdtemp())
    path = "missing.bin"
    with pytest.raises(FileNotFoundError):
        provider.load_chunk(path, 0, CHUNK_SIZE)

def test_get_num_chunks_correct():
    provider = LocalStorageProvider(base_dir=tempfile.mkdtemp())
    path = "testchunksize.bin"
    data = b"a" * (2 * CHUNK_SIZE + 123)
    provider.save(path, data)
    num_chunks = provider.get_num_chunks(path, CHUNK_SIZE)
    assert num_chunks == 3
