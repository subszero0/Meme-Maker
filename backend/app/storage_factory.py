from typing import Union
from app.config import settings
from app.storage import LocalStorageManager, S3StorageManager


def get_storage_manager() -> Union[LocalStorageManager, S3StorageManager]:
    """
    Factory function to get storage manager based on configuration
    Guards the swap behind STORAGE_BACKEND feature flag
    """
    if settings.storage_backend == "local":
        return LocalStorageManager()
    elif settings.storage_backend == "s3":
        return S3StorageManager()
    else:
        raise ValueError(f"Unknown storage backend: {settings.storage_backend}")


# Singleton instance for dependency injection
storage_manager = get_storage_manager() 