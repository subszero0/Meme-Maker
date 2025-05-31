"""
Standalone tests for the InMemoryStorage mock implementation.

This module tests the mock storage without relying on the application integration.
"""
import tempfile
import os
import pytest


def test_standalone_mock_storage():
    """Test InMemoryStorage as a standalone unit."""
    # Import here to avoid module-level import issues
    from app.utils.mock_storage import InMemoryStorage
    
    storage = InMemoryStorage()
    
    # Test that it implements required methods
    assert hasattr(storage, 'upload')
    assert hasattr(storage, 'generate_presigned_url')
    assert hasattr(storage, 'delete')
    assert callable(storage.upload)
    assert callable(storage.generate_presigned_url)
    assert callable(storage.delete)


def test_standalone_upload_and_retrieve():
    """Test basic upload and retrieval without app integration."""
    from app.utils.mock_storage import InMemoryStorage
    
    storage = InMemoryStorage()
    
    # Create a temporary file to upload
    with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as f:
        test_content = b"Hello, World! This is test content."
        f.write(test_content)
        temp_path = f.name
    
    try:
        # Upload the file
        key = "test-file.txt"
        storage.upload(temp_path, key)
        
        # Verify the file is stored correctly
        assert key in storage.list_keys()
        stored_content = storage.get_file_content(key)
        assert stored_content == test_content
        
    finally:
        # Clean up temporary file
        os.unlink(temp_path)


def test_standalone_presigned_url():
    """Test presigned URL generation without app integration."""
    from app.utils.mock_storage import InMemoryStorage
    
    storage = InMemoryStorage()
    
    # Create and upload a test file
    with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as f:
        f.write(b"test content")
        temp_path = f.name
    
    try:
        key = "test-url-file.txt"
        storage.upload(temp_path, key)
        
        # Generate presigned URL
        url = storage.generate_presigned_url(key)
        assert url == f"memory://{key}"
        
        # Test with custom expiration
        url_with_expiry = storage.generate_presigned_url(key, expiration=1800)
        assert url_with_expiry == f"memory://{key}"
        
    finally:
        os.unlink(temp_path)


def test_standalone_delete():
    """Test file deletion without app integration."""
    from app.utils.mock_storage import InMemoryStorage
    
    storage = InMemoryStorage()
    
    # Create and upload a test file
    with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as f:
        f.write(b"test content for deletion")
        temp_path = f.name
    
    try:
        key = "test-delete-file.txt"
        storage.upload(temp_path, key)
        
        # Verify file exists
        assert key in storage.list_keys()
        
        # Delete the file
        storage.delete(key)
        
        # Verify file is gone
        assert key not in storage.list_keys()
        
        # Deleting again should not raise an error
        storage.delete(key)  # Should not raise
        
    finally:
        os.unlink(temp_path)


def test_standalone_complete_flow():
    """Test the complete flow without app integration."""
    from app.utils.mock_storage import InMemoryStorage
    
    storage = InMemoryStorage()
    
    # Create test file
    with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as f:
        test_content = b"Complete flow test content"
        f.write(test_content)
        temp_path = f.name
    
    try:
        key = "complete-flow-test.txt"
        
        # Step 1: Upload
        storage.upload(temp_path, key)
        assert key in storage.list_keys()
        assert storage.get_file_content(key) == test_content
        
        # Step 2: Generate URL
        url = storage.generate_presigned_url(key)
        assert url == f"memory://{key}"
        
        # Step 3: Delete
        storage.delete(key)
        assert key not in storage.list_keys()
        
        # Verify URL generation fails after deletion
        with pytest.raises(FileNotFoundError):
            storage.generate_presigned_url(key)
            
    finally:
        os.unlink(temp_path)


def test_standalone_missing_file_error():
    """Test that operations on missing files fail correctly."""
    from app.utils.mock_storage import InMemoryStorage
    
    storage = InMemoryStorage()
    
    # Test presigned URL for missing file
    with pytest.raises(FileNotFoundError, match="Key 'nonexistent' not found"):
        storage.generate_presigned_url("nonexistent")
    
    # Test get_file_content for missing file  
    with pytest.raises(FileNotFoundError, match="Key 'nonexistent' not found"):
        storage.get_file_content("nonexistent")


def test_standalone_helper_methods():
    """Test the helper methods specific to the mock."""
    from app.utils.mock_storage import InMemoryStorage
    
    storage = InMemoryStorage()
    
    # Start with empty storage
    assert len(storage.list_keys()) == 0
    
    # Add some files
    with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as f1:
        f1.write(b"content1")
        temp_path1 = f1.name
    with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as f2:
        f2.write(b"content2")
        temp_path2 = f2.name
    
    try:
        storage.upload(temp_path1, "file1.txt")
        storage.upload(temp_path2, "file2.txt")
        
        # Test list_keys
        keys = storage.list_keys()
        assert len(keys) == 2
        assert "file1.txt" in keys
        assert "file2.txt" in keys
        
        # Test clear
        storage.clear()
        assert len(storage.list_keys()) == 0
        
    finally:
        os.unlink(temp_path1)
        os.unlink(temp_path2) 