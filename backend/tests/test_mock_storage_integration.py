"""
Integration tests for the InMemoryStorage mock.

This module tests the integration between the mock storage and the storage factory.
"""
import tempfile
import os
import pytest
from unittest.mock import patch


@patch('app.utils.minio_storage.MinIOStorage')
def test_mock_storage_factory_integration(mock_minio_class):
    """Test that we can properly mock the storage factory."""
    # Import after patching to avoid MinIO initialization
    from app.utils.mock_storage import InMemoryStorage
    from app.utils import get_storage, reset_storage
    
    # Reset storage state
    reset_storage()
    
    # Configure the mock to return our InMemoryStorage
    mock_instance = InMemoryStorage()
    mock_minio_class.return_value = mock_instance
    
    # Now get_storage() should return our mock
    storage = get_storage()
    assert isinstance(storage, InMemoryStorage)
    assert storage is mock_instance


def test_mock_storage_with_manual_patching(monkeypatch):
    """Test mock storage with manual patching of the factory function."""
    from app.utils.mock_storage import InMemoryStorage
    from app.utils import reset_storage
    
    # Reset storage state
    reset_storage()
    
    # Create our mock storage instance
    mock_storage = InMemoryStorage()
    
    # Patch the factory function directly
    monkeypatch.setattr('app.utils.get_storage', lambda: mock_storage)
    
    # Test that we get our mock
    from app.utils import get_storage
    storage = get_storage()
    assert isinstance(storage, InMemoryStorage)
    assert storage is mock_storage
    
    # Test basic functionality
    with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as f:
        f.write(b"test content")
        temp_path = f.name
    
    try:
        key = "test-integration.txt"
        storage.upload(temp_path, key)
        url = storage.generate_presigned_url(key)
        assert url == f"memory://{key}"
        storage.delete(key)
        assert key not in storage.list_keys()
    finally:
        os.unlink(temp_path)


@patch.dict(os.environ, {
    'AWS_ACCESS_KEY_ID': 'test',
    'AWS_SECRET_ACCESS_KEY': 'test', 
    'AWS_ENDPOINT_URL': 'http://localhost:9000',
    'S3_BUCKET_NAME': 'test-bucket'
})
def test_mock_storage_with_env_override():
    """Test that we can override environment variables to avoid MinIO connection issues."""
    from app.utils.mock_storage import InMemoryStorage
    
    # Create a standalone mock storage instance
    storage = InMemoryStorage()
    
    # Test basic functionality without any app integration
    with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as f:
        f.write(b"env override test")
        temp_path = f.name
    
    try:
        key = "env-test.txt"
        storage.upload(temp_path, key)
        assert key in storage.list_keys()
        
        url = storage.generate_presigned_url(key)
        assert url == f"memory://{key}"
        
        content = storage.get_file_content(key)
        assert content == b"env override test"
        
        storage.delete(key)
        assert key not in storage.list_keys()
        
    finally:
        os.unlink(temp_path)


def test_storage_interface_compliance():
    """Test that InMemoryStorage properly implements StorageInterface."""
    from app.utils.mock_storage import InMemoryStorage
    from app.utils.storage_interface import StorageInterface
    
    # Test that InMemoryStorage is a subclass of StorageInterface
    assert issubclass(InMemoryStorage, StorageInterface)
    
    # Test that an instance passes isinstance check
    storage = InMemoryStorage()
    assert isinstance(storage, StorageInterface)
    
    # Test that all abstract methods are implemented
    assert hasattr(storage, 'upload')
    assert hasattr(storage, 'generate_presigned_url')
    assert hasattr(storage, 'delete')
    
    # Test that methods are callable
    assert callable(storage.upload)
    assert callable(storage.generate_presigned_url)
    assert callable(storage.delete) 