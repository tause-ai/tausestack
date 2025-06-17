import unittest
import os
import shutil
import json
from pathlib import Path
from tausestack.sdk.storage.backends import LocalStorage

class TestLocalStorage(unittest.TestCase):
    """Test suite for the LocalStorage backend (JSON and Binary)."""

    def setUp(self):
        """Set up temporary storage directories for tests."""
        self.test_base_dir = Path(".test_temp_storage_local")
        self.test_json_path = self.test_base_dir / "json_files"
        self.test_binary_path = self.test_base_dir / "binary_files"
        
        self.storage = LocalStorage(
            base_json_path=str(self.test_json_path),
            base_binary_path=str(self.test_binary_path)
        )
        
        # Ensure the directories are clean before each test
        if self.test_base_dir.exists():
            shutil.rmtree(self.test_base_dir)
        self.test_json_path.mkdir(parents=True, exist_ok=True)
        self.test_binary_path.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up the temporary storage directories after tests."""
        if self.test_base_dir.exists():
            shutil.rmtree(self.test_base_dir)

    # --- JSON Tests ---
    def test_put_and_get_json(self):
        key = "test_data_1"
        data = {"name": "Test Object", "value": 123}
        self.storage.put_json(key, data)
        retrieved_data = self.storage.get_json(key)
        self.assertEqual(retrieved_data, data)

    def test_get_non_existent_json(self):
        retrieved_data = self.storage.get_json("non_existent_key_json")
        self.assertIsNone(retrieved_data)

    def test_overwrite_json(self):
        key = "test_data_overwrite_json"
        original_data = {"version": 1, "content": "original_json"}
        updated_data = {"version": 2, "content": "updated_json"}
        self.storage.put_json(key, original_data)
        self.storage.put_json(key, updated_data)
        retrieved_data = self.storage.get_json(key)
        self.assertEqual(retrieved_data, updated_data)

    def test_delete_json(self):
        key = "test_data_delete_json"
        data = {"status": "to_be_deleted_json"}
        self.storage.put_json(key, data)
        self.storage.delete_json(key)
        retrieved_data = self.storage.get_json(key)
        self.assertIsNone(retrieved_data)
        file_path = self.storage._get_json_file_path(key)
        self.assertFalse(file_path.exists())

    def test_delete_non_existent_json(self):
        try:
            self.storage.delete_json("non_existent_key_for_delete_json")
        except Exception as e:
            self.fail(f"Deleting non-existent JSON key raised an exception: {e}")

    def test_put_with_subdirectories_json(self):
        key = "subdir_json/test_data_subdir"
        data = {"path": "nested/object_json"}
        self.storage.put_json(key, data)
        retrieved_data = self.storage.get_json(key)
        self.assertEqual(retrieved_data, data)
        expected_file_path = self.test_json_path / "subdir_json" / "test_data_subdir.json"
        self.assertTrue(expected_file_path.exists())
        self.assertTrue(expected_file_path.is_file())

    def test_json_key_with_json_suffix(self):
        key_with_suffix = "data_json.json"
        key_without_suffix = "data_json"
        data = {"suffix_test_json": True}

        self.storage.put_json(key_with_suffix, data)
        self.assertEqual(self.storage.get_json(key_with_suffix), data)
        self.assertEqual(self.storage.get_json(key_without_suffix), data)
        self.storage.delete_json(key_with_suffix)

        self.storage.put_json(key_without_suffix, data)
        self.assertEqual(self.storage.get_json(key_with_suffix), data)
        self.assertEqual(self.storage.get_json(key_without_suffix), data)
        self.storage.delete_json(key_without_suffix)

    # --- Binary Tests ---
    def test_put_and_get_binary(self):
        key = "test_binary_data_1.dat"
        binary_data = b"\x00\x01\x02\x03\x04Hello Binary World!\xff\xfe"
        self.storage.put_binary(key, binary_data)
        retrieved_data = self.storage.get_binary(key)
        self.assertEqual(retrieved_data, binary_data)

    def test_get_non_existent_binary(self):
        retrieved_data = self.storage.get_binary("non_existent_binary.dat")
        self.assertIsNone(retrieved_data)

    def test_overwrite_binary(self):
        key = "test_binary_overwrite.log"
        original_data = b"Initial binary content."
        updated_data = b"Updated binary content, much longer and different."
        self.storage.put_binary(key, original_data)
        self.storage.put_binary(key, updated_data) # Overwrite
        retrieved_data = self.storage.get_binary(key)
        self.assertEqual(retrieved_data, updated_data)

    def test_delete_binary(self):
        key = "test_binary_delete.tmp"
        data = b"Temporary binary data to be deleted."
        self.storage.put_binary(key, data)
        self.storage.delete_binary(key)
        retrieved_data = self.storage.get_binary(key)
        self.assertIsNone(retrieved_data)
        file_path = self.storage._get_binary_file_path(key)
        self.assertFalse(file_path.exists())

    def test_delete_non_existent_binary(self):
        try:
            self.storage.delete_binary("non_existent_binary_for_delete.bin")
        except Exception as e:
            self.fail(f"Deleting non-existent binary key raised an exception: {e}")

    def test_put_with_subdirectories_binary(self):
        key = "subdir_binary/another_level/test_data_subdir.img"
        data = b"Image data would go here..."
        self.storage.put_binary(key, data)
        retrieved_data = self.storage.get_binary(key)
        self.assertEqual(retrieved_data, data)
        expected_file_path = self.test_binary_path / "subdir_binary" / "another_level" / "test_data_subdir.img"
        self.assertTrue(expected_file_path.exists())
        self.assertTrue(expected_file_path.is_file())

    def test_binary_key_does_not_add_suffix(self):
        """Ensure binary keys are used as-is, without .json or other suffixes."""
        key = "raw_binary_file"
        data = b"raw data"
        self.storage.put_binary(key, data)
        self.assertIsNotNone(self.storage.get_binary(key))
        expected_file_path = self.test_binary_path / key # No .json suffix
        self.assertTrue(expected_file_path.exists())
        self.storage.delete_binary(key)

if __name__ == '__main__':
    unittest.main()
