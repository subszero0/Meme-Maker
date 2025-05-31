# Storage utilities 
from .storage_interface import StorageInterface
from .minio_storage import MinIOStorage

# Global storage instance (singleton pattern)
_storage_instance: StorageInterface = None


def get_storage() -> StorageInterface:
    """Get the global storage instance (singleton pattern)"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = MinIOStorage()
    return _storage_instance


# For backwards compatibility during transition
def reset_storage() -> None:
    """Reset the storage instance (useful for testing)"""
    global _storage_instance
    _storage_instance = None 