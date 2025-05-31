import pytest
from unittest.mock import patch, Mock
from app.utils import get_storage, reset_storage
from app.utils.storage_interface import StorageInterface
from app.utils.minio_storage import MinIOStorage


def test_storage_interface_definition():
    """Test that the storage interface has the required abstract methods"""
    # Check that all required methods exist on the interface
    required_methods = ['upload', 'generate_presigned_url', 'delete']
    for method in required_methods:
        assert hasattr(StorageInterface, method)


def test_minio_storage_implements_interface():
    """Test that MinIOStorage implements StorageInterface"""
    assert issubclass(MinIOStorage, StorageInterface)


@patch('app.utils.minio_storage.MinIOStorage.__init__', return_value=None)
def test_get_storage_returns_interface_instance(mock_init):
    """Test that get_storage() returns a StorageInterface instance"""
    # Reset storage to test fresh initialization
    reset_storage()
    
    # Mock the initialization to avoid AWS/MinIO connection
    storage = get_storage()
    assert isinstance(storage, MinIOStorage)
    assert isinstance(storage, StorageInterface)


@patch('app.utils.minio_storage.MinIOStorage.__init__', return_value=None)
def test_storage_singleton_pattern(mock_init):
    """Test that get_storage() returns the same instance (singleton)"""
    # Reset storage to test fresh initialization
    reset_storage()
    
    storage1 = get_storage()
    storage2 = get_storage()
    assert storage1 is storage2  # Same object reference


def test_interface_methods_are_abstract():
    """Test that StorageInterface methods are abstract and cannot be instantiated directly"""
    with pytest.raises(TypeError):
        # Should raise TypeError because abstract methods are not implemented
        StorageInterface()


def test_storage_interface_methods_exist():
    """Test that the storage instance has the required interface methods"""
    storage = get_storage()
    
    # Check that all required methods exist
    assert hasattr(storage, 'upload')
    assert hasattr(storage, 'generate_presigned_url') 
    assert hasattr(storage, 'delete')
    
    # Check that methods are callable
    assert callable(storage.upload)
    assert callable(storage.generate_presigned_url)
    assert callable(storage.delete) 