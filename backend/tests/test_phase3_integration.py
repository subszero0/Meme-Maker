"""
Integration tests for Phase 3 components:
- AsyncIO optimization
- Background cleanup tasks
- Metadata caching
- Rate limiting
- Factory patterns
"""
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from backend.app.cache.metadata_cache import MetadataCache
from backend.app.factories.storage_factory import StorageBackend, StorageFactory
from backend.app.middleware.rate_limiter import RateLimiter, TokenBucket
from backend.app.tasks.cleanup import CleanupManager


class TestMetadataCache:
    """Test metadata caching functionality"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        redis_mock = AsyncMock()
        redis_mock.get = AsyncMock(return_value=None)
        redis_mock.setex = AsyncMock(return_value=True)
        redis_mock.keys = AsyncMock(return_value=[])
        redis_mock.delete = AsyncMock(return_value=1)
        return redis_mock

    @pytest.fixture
    def cache(self, mock_redis):
        """Create metadata cache instance"""
        return MetadataCache(mock_redis)

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache, mock_redis):
        """Test cache miss scenario"""
        url = "https://example.com/video.mp4"

        # Mock Redis returning None (cache miss)
        mock_redis.get.return_value = None

        result = await cache.get_metadata(url)

        assert result is None
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_hit(self, cache, mock_redis):
        """Test cache hit scenario"""
        url = "https://example.com/video.mp4"
        cached_data = {
            "url": url,
            "metadata": {"title": "Test Video", "duration": 120},
            "cached_at": datetime.utcnow().isoformat(),
            "cache_version": "1.0",
        }

        # Mock Redis returning cached data
        import json

        mock_redis.get.return_value = json.dumps(cached_data)

        result = await cache.get_metadata(url)

        assert result == cached_data
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_metadata(self, cache, mock_redis):
        """Test setting metadata in cache"""
        url = "https://example.com/video.mp4"
        metadata = {"title": "Test Video", "duration": 120}

        mock_redis.setex.return_value = True

        result = await cache.set_metadata(url, metadata)

        assert result is True
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_url(self, cache, mock_redis):
        """Test cache invalidation"""
        url = "https://example.com/video.mp4"

        # Mock keys and delete operations
        mock_redis.keys.return_value = [
            b"cache:metadata:abc123",
            b"cache:format:abc123",
        ]
        mock_redis.delete.return_value = 2

        result = await cache.invalidate_url(url)

        assert result == 2
        assert mock_redis.keys.call_count == 3  # One for each prefix
        mock_redis.delete.assert_called()


class TestCleanupManager:
    """Test background cleanup functionality"""

    @pytest.fixture
    def mock_job_repository(self):
        """Mock job repository"""
        repo_mock = Mock()
        repo_mock.cleanup_jobs_before = AsyncMock(return_value=5)
        return repo_mock

    @pytest.fixture
    def cleanup_manager(self, mock_job_repository):
        """Create cleanup manager instance"""
        return CleanupManager(mock_job_repository)

    @pytest.mark.asyncio
    async def test_cleanup_expired_jobs(self, cleanup_manager):
        """Test expired job cleanup"""
        with patch.object(cleanup_manager, "_get_expired_jobs", return_value=[]):
            with patch.object(cleanup_manager, "_cleanup_job_files", return_value=3):
                result = await cleanup_manager.cleanup_expired_jobs()

                assert result["jobs_deleted"] == 5
                assert result["files_deleted"] == 3
                assert "cutoff_time" in result

    @pytest.mark.asyncio
    async def test_cleanup_temporary_files(self, cleanup_manager):
        """Test temporary file cleanup"""
        with patch.object(cleanup_manager, "_cleanup_directory") as mock_cleanup:
            mock_cleanup.return_value = {"files_deleted": 10, "size_freed": 1024 * 1024}

            result = await cleanup_manager.cleanup_temporary_files()

            assert result["files_deleted"] == 10
            assert result["size_freed_mb"] == 1.0


class TestRateLimiter:
    """Test rate limiting functionality"""

    def test_token_bucket_consume_success(self):
        """Test successful token consumption"""
        bucket = TokenBucket(capacity=10, tokens=10.0, refill_rate=1.0, last_refill=0)

        result = bucket.consume(5)

        assert result is True
        assert bucket.tokens == 5.0

    def test_token_bucket_consume_failure(self):
        """Test failed token consumption"""
        bucket = TokenBucket(capacity=10, tokens=3.0, refill_rate=1.0, last_refill=0)

        result = bucket.consume(5)

        assert result is False
        assert bucket.tokens == 3.0

    def test_token_bucket_refill(self):
        """Test token bucket refill mechanism"""
        import time

        start_time = time.time()
        bucket = TokenBucket(
            capacity=10,
            tokens=5.0,
            refill_rate=2.0,  # 2 tokens per second
            last_refill=start_time - 1,  # 1 second ago
        )

        # Trigger refill by consuming
        bucket.consume(1)

        # Should have gained ~2 tokens (2 tokens/sec * 1 sec)
        assert bucket.tokens >= 5.0  # 5 original + 2 refilled - 1 consumed

    @pytest.mark.asyncio
    async def test_rate_limiter_allowed(self):
        """Test request allowed by rate limiter"""
        rate_limiter = RateLimiter()

        # Mock request
        request = Mock()
        request.client.host = "127.0.0.1"
        request.url.path = "/api/test"
        request.headers = {}

        is_allowed, info = await rate_limiter.check_rate_limit(request)

        assert is_allowed is True
        assert info is None

    @pytest.mark.asyncio
    async def test_rate_limiter_exceeded(self):
        """Test rate limit exceeded"""
        rate_limiter = RateLimiter()

        # Mock request
        request = Mock()
        request.client.host = "127.0.0.1"
        request.url.path = "/api/test"
        request.headers = {}

        # Exhaust the bucket
        for _ in range(100):  # Exceed the default limit
            await rate_limiter.check_rate_limit(request)

        is_allowed, info = await rate_limiter.check_rate_limit(request)

        assert is_allowed is False
        assert info is not None
        assert info["limit_type"] == "global"


class TestStorageFactory:
    """Test storage factory pattern"""

    def test_create_local_storage(self):
        """Test creating local storage strategy"""
        storage = StorageFactory.create_storage(StorageBackend.LOCAL)

        assert storage is not None
        assert storage.get_backend_type() == StorageBackend.LOCAL

    def test_create_storage_with_string(self):
        """Test creating storage with string backend"""
        storage = StorageFactory.create_storage("local")

        assert storage is not None
        assert storage.get_backend_type() == StorageBackend.LOCAL

    def test_create_unsupported_storage(self):
        """Test creating unsupported storage backend"""
        with pytest.raises(ValueError, match="Unsupported storage backend"):
            StorageFactory.create_storage("unsupported")

    def test_singleton_pattern(self):
        """Test storage factory singleton pattern"""
        storage1 = StorageFactory.create_storage(StorageBackend.LOCAL)
        storage2 = StorageFactory.create_storage(StorageBackend.LOCAL)

        assert storage1 is storage2  # Same instance

    def test_get_default_storage(self):
        """Test getting default storage"""
        with patch(
            "backend.app.factories.storage_factory.get_settings"
        ) as mock_settings:
            mock_settings.return_value.storage_backend = "local"

            storage = StorageFactory.get_default_storage()

            assert storage is not None
            assert storage.get_backend_type() == StorageBackend.LOCAL


class TestAsyncVideoProcessor:
    """Test async video processor (integration with existing components)"""

    @pytest.mark.asyncio
    async def test_concurrent_job_limit(self):
        """Test concurrent job limiting with semaphore"""
        # This would test the semaphore-based concurrency control
        # in the async video processor
        pass

    @pytest.mark.asyncio
    async def test_batch_processing(self):
        """Test batch processing functionality"""
        # This would test processing multiple videos in batches
        pass


class TestPhase3Integration:
    """Test Phase 3 component integration"""

    @pytest.mark.asyncio
    async def test_cache_and_cleanup_integration(self):
        """Test cache and cleanup working together"""
        # Mock Redis
        mock_redis = AsyncMock()
        cache = MetadataCache(mock_redis)

        # Mock repository
        mock_repo = Mock()
        cleanup = CleanupManager(mock_repo)

        # Test that cleanup doesn't interfere with cache
        with patch.object(
            cleanup, "cleanup_expired_jobs", return_value={"jobs_deleted": 0}
        ):
            await cleanup.cleanup_expired_jobs()

        # Cache should still work
        await cache.get_metadata("test_url")
        mock_redis.get.assert_called()

    @pytest.mark.asyncio
    async def test_rate_limiter_with_cache(self):
        """Test rate limiter working with cache"""
        rate_limiter = RateLimiter()

        # Mock request
        request = Mock()
        request.client.host = "127.0.0.1"
        request.url.path = "/api/metadata"
        request.headers = {}

        # Rate limiter should allow requests
        is_allowed, _ = await rate_limiter.check_rate_limit(request)
        assert is_allowed is True

    def test_storage_factory_with_config(self):
        """Test storage factory with configuration"""
        config = {"base_path": "/tmp/test_storage"}

        storage = StorageFactory.create_storage(StorageBackend.LOCAL, config)

        assert storage is not None
        assert storage.get_backend_type() == StorageBackend.LOCAL


if __name__ == "__main__":
    pytest.main([__file__])
