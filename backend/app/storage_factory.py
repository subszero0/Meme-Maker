from app.storage import LocalStorageManager


def get_storage_manager() -> LocalStorageManager:
    """
    Factory function to get storage manager
    Now only supports local storage - S3 migration complete
    """
    # Import settings using the new configuration module
    from app.config.configuration import get_settings

    settings = get_settings()

    if settings.storage_backend == "local":
        return LocalStorageManager()
    else:
        # Force local storage if invalid backend specified
        return LocalStorageManager()


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
