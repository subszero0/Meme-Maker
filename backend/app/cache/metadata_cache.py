"""
Cache module for storing video metadata to reduce repeated extraction calls.
"""
import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote

logger = logging.getLogger(__name__)


class MetadataCache:
    """Cache for video metadata to avoid repeated API calls"""

    def __init__(self, redis_client=None):
        """
        Initialize metadata cache

        Args:
            redis_client: Redis client instance (sync or async)
        """
        self.redis = redis_client
        self.metadata_prefix = "metadata"
        self.format_prefix = "format_metadata"
        self.metadata_ttl = 3600  # 1 hour
        self.format_ttl = 7200  # 2 hours (format metadata is more expensive)

        # Debug: log the type of Redis client being used
        if redis_client is not None:
            logger.info(
                f"🔍 Cache initialized with Redis client type: {type(redis_client)}"
            )
            logger.info(f"🔍 Redis client attributes: {dir(redis_client)[:10]}...")

            # Check if it's an async client by looking for async methods
            if (
                hasattr(redis_client, "__aenter__")
                or "aioredis" in str(type(redis_client))
                or "asyncio" in str(type(redis_client))
            ):
                logger.info("✅ Detected async Redis client")
            else:
                logger.warning(
                    "⚠️ Detected sync Redis client (this may cause async/await errors)"
                )
        else:
            logger.warning("⚠️ Cache initialized with no Redis client")

        # Cache TTL settings (in seconds)
        self.thumbnail_ttl = 86400  # 24 hours for thumbnails

        # Cache key prefixes
        self.thumbnail_prefix = "cache:thumbnail:"

    def _generate_url_hash(self, url: str) -> str:
        """Generate a consistent hash for URL-based cache keys"""
        return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]

    def _generate_cache_key(self, prefix: str, url: str, **kwargs) -> str:
        """Generate cache key with optional parameters"""
        url_hash = self._generate_url_hash(url)

        if kwargs:
            # Sort kwargs for consistent key generation
            params = sorted(kwargs.items())
            param_str = "_".join(f"{k}_{v}" for k, v in params)
            return f"{prefix}{url_hash}_{param_str}"

        return f"{prefix}{url_hash}"

    async def get_metadata(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached video metadata

        Args:
            url: Video URL to look up

        Returns:
            Cached metadata dictionary or None if not found/expired
        """
        try:
            if self.redis is None:
                logger.debug("Redis not available, skipping cache lookup")
                return None

            cache_key = self._generate_cache_key(self.metadata_prefix, url)

            # Get from cache - handle both async and sync Redis clients
            try:
                result = self.redis.get(cache_key)

                # Handle async vs sync Redis clients
                if asyncio.iscoroutine(result):
                    result = await result

                if result:
                    cache_entry = json.loads(result)

                    # Validate cache entry structure
                    if "metadata" in cache_entry and "cached_at" in cache_entry:
                        cached_time = datetime.fromisoformat(cache_entry["cached_at"])
                        if datetime.utcnow() - cached_time < timedelta(
                            seconds=self.metadata_ttl
                        ):
                            logger.info(f"✅ Cache hit for metadata: {url}")
                            return cache_entry
                        else:
                            logger.info(f"⏰ Cache expired for metadata: {url}")
                    else:
                        logger.warning(f"⚠️ Invalid cache entry structure for: {url}")
                else:
                    logger.debug(f"Cache miss for metadata: {url}")

            except Exception as redis_error:
                logger.error(f"Redis get failed: {redis_error}")

        except Exception as e:
            logger.error(f"Failed to get metadata from cache: {str(e)}")

        return None

    async def set_metadata(self, url: str, metadata: Dict[str, Any]) -> bool:
        """
        Cache video metadata

        Args:
            url: Video URL
            metadata: Metadata dictionary to cache

        Returns:
            True if successfully cached, False otherwise
        """
        try:
            if self.redis is None:
                logger.debug("Redis not available, skipping cache storage")
                return False

            cache_key = self._generate_cache_key(self.metadata_prefix, url)

            # Add cache metadata
            cache_entry = {
                "url": url,
                "metadata": metadata,
                "cached_at": datetime.utcnow().isoformat(),
                "cache_version": "1.0",
            }

            # Store with TTL - handle both async and sync Redis clients
            try:
                result = self.redis.setex(
                    cache_key, self.metadata_ttl, json.dumps(cache_entry, default=str)
                )

                # Handle async vs sync Redis clients
                if asyncio.iscoroutine(result):
                    result = await result

                # Convert result to boolean (Redis setex returns True on success)
                success = bool(result) if result is not None else False
                if success:
                    logger.info(f"✅ Cached metadata for: {url}")
                else:
                    logger.warning(
                        f"⚠️ Redis setex returned {result} for metadata cache"
                    )
                return success
            except Exception as redis_error:
                logger.error(f"Redis setex failed: {redis_error}")
                return False

        except Exception as e:
            logger.error(f"Failed to cache metadata: {str(e)}")
            return False

    async def get_format_metadata(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached detailed format metadata

        Args:
            url: Video URL to look up

        Returns:
            Cached detailed metadata dictionary or None if not found/expired
        """
        try:
            if self.redis is None:
                logger.debug("Redis not available, skipping format cache lookup")
                return None

            cache_key = self._generate_cache_key(self.format_prefix, url)

            # Get from cache - handle both async and sync Redis clients
            try:
                result = self.redis.get(cache_key)

                # Handle async vs sync Redis clients
                if asyncio.iscoroutine(result):
                    result = await result

                if result:
                    cache_entry = json.loads(result)

                    # Validate cache entry structure
                    if "metadata" in cache_entry and "cached_at" in cache_entry:
                        cached_time = datetime.fromisoformat(cache_entry["cached_at"])
                        if datetime.utcnow() - cached_time < timedelta(
                            seconds=self.format_ttl
                        ):
                            logger.info(f"✅ Cache hit for format metadata: {url}")
                            return cache_entry
                        else:
                            logger.info(f"⏰ Format cache expired for: {url}")
                    else:
                        logger.warning(
                            f"⚠️ Invalid format cache entry structure for: {url}"
                        )
                else:
                    logger.debug(f"Format cache miss for: {url}")

            except Exception as redis_error:
                logger.error(f"Redis get failed: {redis_error}")

        except Exception as e:
            logger.error(f"Failed to get format metadata from cache: {str(e)}")

        return None

    async def set_format_metadata(self, url: str, metadata: Dict[str, Any]) -> bool:
        """
        Cache detailed format metadata (for /metadata/extract endpoint)

        Args:
            url: Video URL
            metadata: Detailed metadata with formats to cache

        Returns:
            True if successfully cached, False otherwise
        """
        try:
            if self.redis is None:
                logger.debug("Redis not available, skipping format cache storage")
                return False

            cache_key = self._generate_cache_key(self.format_prefix, url)

            # Add cache metadata
            cache_entry = {
                "url": url,
                "metadata": metadata,
                "cached_at": datetime.utcnow().isoformat(),
                "cache_version": "1.0",
            }

            # Store with TTL - handle both async and sync Redis clients
            try:
                result = self.redis.setex(
                    cache_key, self.format_ttl, json.dumps(cache_entry, default=str)
                )

                # Handle async vs sync Redis clients
                if asyncio.iscoroutine(result):
                    result = await result

                # Convert result to boolean (Redis setex returns True on success)
                success = bool(result) if result is not None else False
                if success:
                    logger.info(f"✅ Cached format metadata for: {url}")
                else:
                    logger.warning(
                        f"⚠️ Redis setex returned {result} for format metadata cache"
                    )
                return success
            except Exception as redis_error:
                logger.error(f"Redis setex failed: {redis_error}")
                return False

        except Exception as e:
            logger.error(f"Failed to cache format metadata: {str(e)}")
            return False

    async def get_format_info(
        self, url: str, quality: str = "best"
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached format detection results

        Args:
            url: Video URL
            quality: Quality preference (best, worst, specific format)

        Returns:
            Cached format information or None if not found
        """
        try:
            cache_key = self._generate_cache_key(
                self.format_prefix, url, quality=quality
            )

            cached_data = await self.redis.get(cache_key)

            if cached_data:
                format_info = json.loads(cached_data)
                logger.debug(f"Cache hit for format info: {url} (quality: {quality})")

                return format_info

            logger.debug(f"Cache miss for format info: {url} (quality: {quality})")
            return None

        except Exception as e:
            logger.error(f"Failed to get format info from cache: {str(e)}")
            return None

    async def set_format_info(
        self, url: str, quality: str, format_info: Dict[str, Any]
    ) -> bool:
        """
        Cache format detection results

        Args:
            url: Video URL
            quality: Quality preference
            format_info: Format information to cache

        Returns:
            True if successfully cached, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(
                self.format_prefix, url, quality=quality
            )

            cache_entry = {
                "url": url,
                "quality": quality,
                "format_info": format_info,
                "cached_at": datetime.utcnow().isoformat(),
                "cache_version": "1.0",
            }

            success = await self.redis.setex(
                cache_key, self.format_ttl, json.dumps(cache_entry, default=str)
            )

            if success:
                logger.debug(f"Cached format info for: {url} (quality: {quality})")

            return bool(success)

        except Exception as e:
            logger.error(f"Failed to cache format info: {str(e)}")
            return False

    async def get_thumbnail_url(self, url: str) -> Optional[str]:
        """
        Get cached thumbnail URL

        Args:
            url: Video URL

        Returns:
            Cached thumbnail URL or None if not found
        """
        try:
            cache_key = self._generate_cache_key(self.thumbnail_prefix, url)
            thumbnail_url = await self.redis.get(cache_key)

            if thumbnail_url:
                logger.debug(f"Cache hit for thumbnail: {url}")
                return (
                    thumbnail_url.decode("utf-8")
                    if isinstance(thumbnail_url, bytes)
                    else thumbnail_url
                )

            return None

        except Exception as e:
            logger.error(f"Failed to get thumbnail from cache: {str(e)}")
            return None

    async def set_thumbnail_url(self, url: str, thumbnail_url: str) -> bool:
        """
        Cache thumbnail URL

        Args:
            url: Video URL
            thumbnail_url: Thumbnail URL to cache

        Returns:
            True if successfully cached, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(self.thumbnail_prefix, url)

            success = await self.redis.setex(
                cache_key, self.thumbnail_ttl, thumbnail_url
            )

            if success:
                logger.debug(f"Cached thumbnail for: {url}")

            return bool(success)

        except Exception as e:
            logger.error(f"Failed to cache thumbnail: {str(e)}")
            return False

    async def invalidate_url(self, url: str) -> int:
        """
        Invalidate all cache entries for a specific URL

        Args:
            url: Video URL to invalidate

        Returns:
            Number of cache entries deleted
        """
        try:
            url_hash = self._generate_url_hash(url)

            # Find all keys related to this URL
            patterns = [
                f"{self.metadata_prefix}{url_hash}*",
                f"{self.format_prefix}{url_hash}*",
                f"{self.thumbnail_prefix}{url_hash}*",
            ]

            deleted_count = 0

            for pattern in patterns:
                keys = await self.redis.keys(pattern)
                if keys:
                    deleted = await self.redis.delete(*keys)
                    deleted_count += deleted

            if deleted_count > 0:
                logger.info(f"Invalidated {deleted_count} cache entries for: {url}")

            return deleted_count

        except Exception as e:
            logger.error(f"Failed to invalidate cache for URL: {str(e)}")
            return 0

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache usage statistics

        Returns:
            Dictionary with cache statistics
        """
        try:
            stats = {}

            # Count keys by type
            for cache_type, prefix in [
                ("metadata", self.metadata_prefix),
                ("format", self.format_prefix),
                ("thumbnail", self.thumbnail_prefix),
            ]:
                keys = await self.redis.keys(f"{prefix}*")
                stats[f"{cache_type}_count"] = len(keys)

            return stats

        except Exception as e:
            logger.error(f"Failed to get cache stats: {str(e)}")
            return {}

    async def cleanup_expired_cache(self) -> Dict[str, int]:
        """
        Clean up expired cache entries (Redis handles TTL automatically)
        This method can be used for manual cleanup if needed

        Returns:
            Dictionary with cleanup statistics
        """
        try:
            # Redis automatically handles TTL expiration
            # This method can be used for additional cleanup logic

            stats = await self.get_cache_stats()

            logger.info(f"Cache cleanup completed. Current stats: {stats}")

            return {
                "expired_entries_removed": 0,  # Redis handles this automatically
                "current_cache_size": sum(
                    stats.get(f"{cache_type}_count", 0)
                    for cache_type in ["metadata", "format", "thumbnail"]
                ),
            }

        except Exception as e:
            logger.error(f"Cache cleanup failed: {str(e)}")
            return {"expired_entries_removed": 0, "current_cache_size": 0}

    async def _update_access_time(self, cache_key: str) -> None:
        """Update access time for LRU tracking"""
        try:
            access_key = f"access:{cache_key}"
            await self.redis.setex(access_key, 86400, datetime.utcnow().isoformat())
        except Exception as e:
            logger.debug(f"Failed to update access time: {str(e)}")

    async def _track_cache_operation(
        self, operation_type: str, operation: str, count: int = 1
    ) -> None:
        """Track cache operations for metrics"""
        try:
            metrics_key = f"cache_metrics:{operation_type}:{operation}"
            await self.redis.incrby(metrics_key, count)
            await self.redis.expire(metrics_key, 86400)  # Expire metrics after 24 hours
        except Exception as e:
            logger.debug(f"Failed to track cache operation: {str(e)}")

    async def _get_cache_metrics(self) -> Dict[str, int]:
        """Get cache operation metrics"""
        try:
            metrics = {}

            # Get all metric keys
            metric_keys = await self.redis.keys("cache_metrics:*")

            for key in metric_keys:
                if isinstance(key, bytes):
                    key = key.decode("utf-8")

                value = await self.redis.get(key)
                if value:
                    # Extract metric name from key
                    metric_name = key.replace("cache_metrics:", "").replace(":", "_")
                    metrics[metric_name] = int(value)

            return metrics

        except Exception as e:
            logger.debug(f"Failed to get cache metrics: {str(e)}")
            return {}


# Cache decorator for functions
def cache_metadata(ttl: int = 3600):
    """
    Decorator to cache function results in Redis

    Args:
        ttl: Time to live in seconds
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would need to be implemented based on specific caching needs
            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Utility functions
async def warm_cache_for_popular_urls(
    cache: MetadataCache, urls: List[str]
) -> Dict[str, bool]:
    """
    Warm cache for a list of popular URLs

    Args:
        cache: MetadataCache instance
        urls: List of URLs to warm

    Returns:
        Dictionary mapping URLs to success status
    """
    results = {}

    for url in urls:
        try:
            # Check if already cached
            if await cache.get_metadata(url):
                results[url] = True
                continue

            # This would need integration with actual metadata extraction
            # For now, just mark as processed
            results[url] = False

        except Exception as e:
            logger.error(f"Failed to warm cache for {url}: {str(e)}")
            results[url] = False

    return results
