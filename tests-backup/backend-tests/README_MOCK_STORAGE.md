# Mock Storage for Testing

This directory contains an in-memory mock storage implementation that adheres to the `StorageInterface` for use in tests.

## Overview

The `InMemoryStorage` class provides a fake storage backend that stores files in memory instead of connecting to actual MinIO/S3 storage. This enables fast, reliable, and isolated tests.

## Files

- `app/utils/mock_storage.py` - The `InMemoryStorage` implementation
- `tests/conftest.py` - Contains the `mock_storage` pytest fixture
- `tests/test_mock_storage_standalone.py` - Unit tests for the mock storage
- `tests/test_mock_storage_integration.py` - Integration tests with the storage factory
- `tests/test_example_with_mock_storage.py` - Examples of using the mock in tests

## Usage

### Basic Usage

Use the `mock_storage` fixture in any test that needs to mock storage operations:

```python
def test_my_function(mock_storage):
    from app.utils import get_storage
    
    # get_storage() now returns the mock
    storage = get_storage()
    assert storage is mock_storage
    
    # Use storage normally
    storage.upload("path/to/file.txt", "key")
    url = storage.generate_presigned_url("key")
    storage.delete("key")
```

### Features

The `InMemoryStorage` mock provides:

- **`upload(local_path, key)`** - Reads file from `local_path` and stores content in memory under `key`
- **`generate_presigned_url(key, expiration=3600)`** - Returns `"memory://{key}"` 
- **`delete(key)`** - Removes the file from memory
- **`get_file_content(key)`** - Helper method to retrieve stored content (for testing)
- **`list_keys()`** - Helper method to list all stored keys (for testing)
- **`clear()`** - Helper method to clear all stored files (for testing)

### Error Handling

The mock handles errors consistently with the real storage:

- `generate_presigned_url()` and `get_file_content()` raise `FileNotFoundError` for missing keys
- `delete()` for non-existent keys logs a warning but doesn't raise an error
- `upload()` can raise file I/O errors if the source file is invalid

### Test Isolation

Each test gets a fresh, empty `InMemoryStorage` instance. The fixture automatically:

1. Resets the storage singleton
2. Creates a new mock instance
3. Patches `get_storage()` to return the mock
4. Cleans up the mock after the test

### Example Test

```python
def test_clip_storage_workflow(mock_storage):
    """Test storing and retrieving a video clip."""
    from app.utils import get_storage
    
    storage = get_storage()
    
    # Create a fake video file
    with tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.mp4') as f:
        f.write(b"fake video content")
        temp_path = f.name
    
    try:
        # Store the clip
        clip_key = "clips/test-clip.mp4"
        storage.upload(temp_path, clip_key)
        
        # Verify it's stored
        assert clip_key in storage.list_keys()
        
        # Generate download URL
        url = storage.generate_presigned_url(clip_key)
        assert url == f"memory://{clip_key}"
        
        # Verify content
        content = storage.get_file_content(clip_key)
        assert content == b"fake video content"
        
        # Clean up
        storage.delete(clip_key)
        assert clip_key not in storage.list_keys()
        
    finally:
        os.unlink(temp_path)
```

## Benefits

1. **Fast** - No network I/O or external dependencies
2. **Reliable** - No connection failures or timeouts
3. **Isolated** - Each test gets a clean storage state
4. **Deterministic** - Consistent behavior across test runs
5. **Easy Debugging** - Simple in-memory operations with helper methods

## Thread Safety

The mock storage is designed for single-threaded test execution. If tests run in parallel, each test process gets its own isolated instance.

## Integration with Real Storage

The mock implements the same `StorageInterface` as the real `MinIOStorage`, ensuring that:

- Tests exercise the same API surface
- Code can switch between mock and real storage seamlessly
- Integration tests can verify the interface compatibility

## Limitations

- Does not test actual S3/MinIO compatibility
- No network error simulation
- No file size or storage limits
- Presigned URLs are fake (`memory://` scheme)

For end-to-end testing with real storage, use the E2E test suite instead. 