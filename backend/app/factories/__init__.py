"""
Factory patterns package.
Contains storage factory and strategy patterns for pluggable components.
"""

from .storage_factory import StorageFactory, StorageStrategy, StorageBackend

__all__ = ["StorageFactory", "StorageStrategy", "StorageBackend"] 