"""
Cache package for metadata and video information caching.
Provides Redis-based caching for improved performance.
"""

from .metadata_cache import MetadataCache

__all__ = ["MetadataCache"] 