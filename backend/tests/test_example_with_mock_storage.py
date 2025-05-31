"""
Example test showing how to use the mock storage in tests.

This demonstrates how other test files can use the mock_storage fixture
to test functionality that depends on storage operations.
"""
import tempfile
import os
import pytest


def test_example_function_using_storage(mock_storage):
    """Example test using the mock storage fixture."""
    from app.utils import get_storage
    
    # The fixture ensures get_storage() returns our mock
    storage = get_storage()
    assert storage is mock_storage
    
    # Create a test file
    with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as f:
        f.write(b"test data for example")
        temp_path = f.name
    
    try:
        # Test upload
        storage.upload(temp_path, "example.txt")
        assert "example.txt" in storage.list_keys()
        
        # Test URL generation
        url = storage.generate_presigned_url("example.txt")
        assert url == "memory://example.txt"
        
        # Test content retrieval
        content = storage.get_file_content("example.txt")
        assert content == b"test data for example"
        
        # Test deletion
        storage.delete("example.txt")
        assert "example.txt" not in storage.list_keys()
        
    finally:
        os.unlink(temp_path)


def test_example_api_logic_with_storage(mock_storage):
    """Example showing how to test API logic that uses storage."""
    from app.utils import get_storage
    
    storage = get_storage()
    
    # Simulate an API function that stores and retrieves files
    def api_store_clip(file_path: str, clip_id: str) -> str:
        """Example API function that stores a clip and returns a URL."""
        storage.upload(file_path, f"clips/{clip_id}.mp4")
        return storage.generate_presigned_url(f"clips/{clip_id}.mp4")
    
    def api_delete_clip(clip_id: str) -> None:
        """Example API function that deletes a clip."""
        storage.delete(f"clips/{clip_id}.mp4")
    
    # Test the API functions
    with tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.mp4') as f:
        f.write(b"fake video content")
        temp_path = f.name
    
    try:
        # Test storing a clip
        clip_id = "test-clip-123"
        url = api_store_clip(temp_path, clip_id)
        
        # Verify it was stored
        assert f"clips/{clip_id}.mp4" in storage.list_keys()
        assert url == f"memory://clips/{clip_id}.mp4"
        
        # Test deleting the clip
        api_delete_clip(clip_id)
        assert f"clips/{clip_id}.mp4" not in storage.list_keys()
        
    finally:
        os.unlink(temp_path)


def test_multiple_operations_with_storage(mock_storage):
    """Example showing multiple operations in a single test."""
    from app.utils import get_storage
    
    storage = get_storage()
    
    # Create multiple test files
    test_files = []
    for i in range(3):
        with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as f:
            f.write(f"content for file {i}".encode())
            test_files.append((f.name, f"file_{i}.txt"))
    
    try:
        # Upload all files
        for temp_path, key in test_files:
            storage.upload(temp_path, key)
        
        # Verify all files are stored
        keys = storage.list_keys()
        assert len(keys) == 3
        for _, key in test_files:
            assert key in keys
        
        # Generate URLs for all files
        urls = []
        for _, key in test_files:
            url = storage.generate_presigned_url(key)
            urls.append(url)
            assert url == f"memory://{key}"
        
        # Verify content of each file
        for i, (_, key) in enumerate(test_files):
            content = storage.get_file_content(key)
            expected = f"content for file {i}".encode()
            assert content == expected
        
        # Delete files one by one
        for _, key in test_files:
            storage.delete(key)
        
        # Verify all files are gone
        assert len(storage.list_keys()) == 0
        
    finally:
        # Clean up temp files
        for temp_path, _ in test_files:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass


def test_error_handling_with_storage(mock_storage):
    """Example showing error handling with mock storage."""
    from app.utils import get_storage
    
    storage = get_storage()
    
    # Test accessing non-existent file
    with pytest.raises(FileNotFoundError):
        storage.generate_presigned_url("non-existent.txt")
    
    with pytest.raises(FileNotFoundError):
        storage.get_file_content("non-existent.txt")
    
    # Test that deleting non-existent file doesn't raise an error
    storage.delete("non-existent.txt")  # Should not raise
    
    # Test uploading a file and then accessing it
    with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as f:
        f.write(b"error test content")
        temp_path = f.name
    
    try:
        storage.upload(temp_path, "error-test.txt")
        
        # This should work
        url = storage.generate_presigned_url("error-test.txt")
        assert url == "memory://error-test.txt"
        
        # Delete and then try to access again
        storage.delete("error-test.txt")
        
        # This should fail
        with pytest.raises(FileNotFoundError):
            storage.generate_presigned_url("error-test.txt")
            
    finally:
        os.unlink(temp_path) 