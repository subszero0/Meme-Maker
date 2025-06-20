from typing import Union
from app.storage import LocalStorageManager, S3StorageManager

def get_storage_manager() -> Union[LocalStorageManager, S3StorageManager]:
    """
    Factory function to get storage manager based on configuration
    Guards the swap behind STORAGE_BACKEND feature flag
    """
    # Import settings using the new configuration module
    from app.config.configuration import get_settings
    settings = get_settings()
    
    if settings.storage_backend == "local":
        return LocalStorageManager()
    elif settings.storage_backend == "s3":
        return S3StorageManager()
    else:
        raise ValueError(f"Unknown storage backend: {settings.storage_backend}")


# Singleton instance for dependency injection - initialize when first accessed
_storage_manager = None

def get_storage_instance():
    """Get singleton storage manager instance"""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = get_storage_manager()
    return _storage_manager

# For backward compatibility
storage_manager = get_storage_instance() 