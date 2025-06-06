# Tests for S3JsonStorage backend in tausestack.sdk.storage.backends
import pytest
import os
import json
import boto3
from moto import mock_aws

from tausestack.sdk.storage.backends import S3JsonStorage

TEST_BUCKET_NAME = "test-tausestack-s3-storage-bucket"

@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1" # Moto needs a region

@pytest.fixture(scope="function")
def s3_client_fixture(aws_credentials):
    """Provides a mocked S3 client using moto."""
    with mock_aws():
        client = boto3.client("s3", region_name=os.environ["AWS_DEFAULT_REGION"])
        yield client

@pytest.fixture(scope="function")
def s3_storage_backend(s3_client_fixture):
    """Provides an S3JsonStorage instance with a mocked S3 client and a test bucket."""
    # Create the bucket in the mocked S3 environment
    try:
        s3_client_fixture.create_bucket(Bucket=TEST_BUCKET_NAME)
    except Exception as e:
        # This might happen if moto's state isn't perfectly clean or due to specific moto versions.
        # For robust tests, ensuring the bucket exists is key.
        print(f"Note: Could not create bucket {TEST_BUCKET_NAME} during fixture setup (possibly pre-existing in mock): {e}")

    storage = S3JsonStorage(bucket_name=TEST_BUCKET_NAME, s3_client=s3_client_fixture)
    yield storage
    
    # Optional: Cleanup after tests. Moto's mock_aws context usually handles this.
    # If issues with state leakage between tests, one might add explicit cleanup here:
    # try:
    #     objects = s3_client_fixture.list_objects_v2(Bucket=TEST_BUCKET_NAME)
    #     if 'Contents' in objects:
    #         delete_keys = {'Objects': [{'Key': obj['Key']} for obj in objects['Contents']]}
    #         s3_client_fixture.delete_objects(Bucket=TEST_BUCKET_NAME, Delete=delete_keys)
    #     s3_client_fixture.delete_bucket(Bucket=TEST_BUCKET_NAME)
    # except Exception as e:
    #     print(f"Error during S3 cleanup: {e}")


# --- Test Cases ---

def test_put_get_delete_simple_key(s3_storage_backend: S3JsonStorage):
    key = "test_object.json"
    data = {"message": "Hello, S3!", "version": 1}
    s3_storage_backend.put(key, data)
    retrieved_data = s3_storage_backend.get(key)
    assert retrieved_data is not None
    assert retrieved_data == data
    s3_storage_backend.delete(key)
    assert s3_storage_backend.get(key) is None

def test_put_overwrite_existing_key(s3_storage_backend: S3JsonStorage):
    key = "overwrite_test.json"
    initial_data = {"status": "initial"}
    updated_data = {"status": "updated"}
    s3_storage_backend.put(key, initial_data)
    assert s3_storage_backend.get(key) == initial_data
    s3_storage_backend.put(key, updated_data)
    assert s3_storage_backend.get(key) == updated_data
    s3_storage_backend.delete(key)

def test_get_non_existent_key(s3_storage_backend: S3JsonStorage):
    key = "does_not_exist.json"
    assert s3_storage_backend.get(key) is None

def test_delete_non_existent_key(s3_storage_backend: S3JsonStorage):
    key = "phantom_key.json"
    try:
        s3_storage_backend.delete(key)
    except Exception as e:
        pytest.fail(f"Deleting non-existent key raised an exception: {e}")

def test_put_get_delete_nested_key(s3_storage_backend: S3JsonStorage):
    key = "path/to/nested/object.json"
    data = {"detail": "This is a nested object."}
    s3_storage_backend.put(key, data)
    assert s3_storage_backend.get(key) == data
    s3_storage_backend.delete(key)
    assert s3_storage_backend.get(key) is None

def test_put_non_serializable_value(s3_storage_backend: S3JsonStorage):
    key = "unserializable.json"
    data = {"value": {1, 2, 3}}  # A set is not JSON serializable by default
    with pytest.raises(TypeError):
        s3_storage_backend.put(key, data)
    assert s3_storage_backend.get(key) is None

def test_get_corrupted_json_in_s3(s3_storage_backend: S3JsonStorage, s3_client_fixture):
    key = "corrupted_data.json"
    corrupted_content = "this is not valid json { definitely not"
    s3_client_fixture.put_object(Bucket=TEST_BUCKET_NAME, Key=key, Body=corrupted_content.encode('utf-8'))
    with pytest.raises(json.JSONDecodeError):
        s3_storage_backend.get(key)
    s3_storage_backend.delete(key)

def test_s3_storage_instantiation_with_default_client(aws_credentials):
    """Test S3JsonStorage instantiation without an explicit s3_client."""
    with mock_aws():
        # Ensure the bucket exists for this specific test scenario
        temp_s3_client = boto3.client("s3", region_name=os.environ["AWS_DEFAULT_REGION"])
        try:
            temp_s3_client.create_bucket(Bucket=TEST_BUCKET_NAME)
        except temp_s3_client.exceptions.BucketAlreadyOwnedByYou:
            pass # Bucket already exists, which is fine for the test
        except Exception as e:
            print(f"Note: Bucket creation issue in default client test: {e}")
            
        storage = S3JsonStorage(bucket_name=TEST_BUCKET_NAME)
        assert storage.bucket_name == TEST_BUCKET_NAME
        assert storage.s3_client is not None
        key = "default_client_test.json"
        data = {"works": True}
        storage.put(key, data)
        assert storage.get(key) == data
        storage.delete(key)
