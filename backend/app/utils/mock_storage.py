"""
In-memory mock storage implementation for testing.

This module provides a fake storage backend that adheres to StorageInterface,
storing files in memory for use in tests.
"""
import logging
from typing import Dict
from .storage_interface import StorageInterface

logger = logging.getLogger(__name__)


class InMemoryStorage(StorageInterface):
    """In-memory storage implementation for testing purposes."""
    
    def __init__(self):
        """Initialize the in-memory storage with an empty store."""
        self._store: Dict[str, bytes] = {}
        logger.debug("Initialized InMemoryStorage")
    
    def upload(self, local_path: str, key: str) -> None:
        """Upload a file from local_path to the storage under key."""
        try:
            with open(local_path, 'rb') as f:
                file_content = f.read()
            self._store[key] = file_content
            logger.info(f"Uploaded {local_path} as {key} ({len(file_content)} bytes)")
        except Exception as e:
            logger.error(f"Failed to upload {local_path}: {e}")
            raise
    
    def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        """Return a mock presigned URL for the given key."""
        if key not in self._store:
            raise FileNotFoundError(f"Key '{key}' not found in storage")
        
        url = f"memory://{key}"
        logger.info(f"Generated mock presigned URL for {key}: {url}")
        return url
    
    def delete(self, key: str) -> None:
        """Delete the object identified by key."""
        if key in self._store:
            del self._store[key]
            logger.info(f"Deleted object {key}")
        else:
            logger.warning(f"Attempted to delete non-existent key: {key}")
    
    def get_file_content(self, key: str) -> bytes:
        """Get file content by key (test helper method)."""
        if key not in self._store:
            raise FileNotFoundError(f"Key '{key}' not found in storage")
        return self._store[key]
    
    def list_keys(self) -> list[str]:
        """List all stored keys (test helper method)."""
        return list(self._store.keys())
    
    def clear(self) -> None:
        """Clear all stored files (test helper method)."""
        self._store.clear()
        logger.debug("Cleared all files from InMemoryStorage") 