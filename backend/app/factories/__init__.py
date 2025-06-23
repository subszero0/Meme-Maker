"""
Factory patterns package.
Contains storage factory and strategy patterns for pluggable components.
"""

from .storage_factory import StorageBackend, StorageFactory, StorageStrategy

__all__ = ["StorageFactory", "StorageStrategy", "StorageBackend"]
