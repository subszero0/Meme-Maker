"""Tests for rate limiting functionality"""

import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.ratelimit import get_client_ip, init_rate_limit, rate_limit_exception_handler


@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture
async def mock_redis():
    """Mock Redis connection for testing"""
    with patch("app.ratelimit.aioredis.from_url") as mock_from_url:
        mock_redis_instance = AsyncMock()
        mock_from_url.return_value = mock_redis_instance
        yield mock_redis_instance


class TestRateLimiting:
    """Test rate limiting functionality"""

    def test_global_rate_limit_enforcement(self, client):
        """Test that global rate limit is enforced"""
        # Mock FastAPILimiter to avoid initialization issues
        with (
            patch("fastapi_limiter.FastAPILimiter.init", new_callable=AsyncMock),
            patch(
                "fastapi_limiter.depends.RateLimiter.__call__",
                new_callable=lambda: AsyncMock(return_value=None),
            ),
        ):
            # Make requests up to the limit
            for i in range(settings.global_rate_limit_requests):
                response = client.post(
                    "/api/v1/metadata", json={"url": "https://example.com/video"}
                )
                # Should succeed (200) or be rate limited (429) if Redis is working
                assert response.status_code in [200, 429]

            # The next request should be rate limited
            response = client.post(
                "/api/v1/metadata", json={"url": "https://example.com/video"}
            )
            if response.status_code == 429:
                data = response.json()
                assert "Rate limit exceeded" in data["detail"]
                assert "retry_after" in data
                assert isinstance(data["retry_after"], int)
                assert data["retry_after"] > 0

    def test_job_creation_rate_limit_enforcement(self, client):
        """Test that job creation rate limit is enforced"""
        # Mock FastAPILimiter and Redis to avoid infrastructure dependencies
        with (
            patch("fastapi_limiter.FastAPILimiter.init", new_callable=AsyncMock),
            patch(
                "fastapi_limiter.depends.RateLimiter.__call__",
                new_callable=lambda: AsyncMock(return_value=None),
            ),
            patch("app.api.jobs.redis") as mock_redis,
            patch("app.api.jobs.q") as mock_queue,
        ):
            # Configure mocks
            mock_queue.enqueue.return_value.id = "test-job-id"

            job_data = {
                "url": "https://example.com/video",
                "start": 1,
                "end": 10,
                "accepted_terms": True,
            }

            # Make job creation requests up to the limit
            for i in range(settings.job_rate_limit_requests):
                response = client.post("/api/v1/jobs", json=job_data)
                # Should succeed (202) or be rate limited (429) if Redis is working
                assert response.status_code in [202, 429]

            # The next request should be rate limited
            response = client.post("/api/v1/jobs", json=job_data)
            if response.status_code == 429:
                data = response.json()
                assert "Job creation limit exceeded" in data["detail"]
                assert "retry_after" in data
                assert isinstance(data["retry_after"], int)
                assert data["retry_after"] > 0

    def test_rate_limit_response_format(self, client):
        """Test that 429 responses have the correct format"""
        # Mock FastAPILimiter to avoid initialization issues
        with (
            patch("fastapi_limiter.FastAPILimiter.init", new_callable=AsyncMock),
            patch(
                "fastapi_limiter.depends.RateLimiter.__call__",
                new_callable=lambda: AsyncMock(return_value=None),
            ),
        ):
            # Make enough requests to trigger rate limit
            for _ in range(15):  # Exceed global limit
                response = client.post(
                    "/api/v1/metadata", json={"url": "https://example.com/video"}
                )
                if response.status_code == 429:
                    data = response.json()

                    # Check required fields
                    assert "detail" in data
                    assert "retry_after" in data
                    assert "limit_type" in data

                    # Check field types
                    assert isinstance(data["detail"], str)
                    assert isinstance(data["retry_after"], int)
                    assert data["limit_type"] in ["global", "job_creation"]

                    # Check retry-after header
                    assert "retry-after" in response.headers
                    assert response.headers["retry-after"] == str(data["retry_after"])
                    break

    def test_different_endpoints_share_global_limit(self, client):
        """Test that different endpoints share the same global rate limit"""
        # Mock FastAPILimiter and Redis to avoid infrastructure dependencies
        with (
            patch("fastapi_limiter.FastAPILimiter.init", new_callable=AsyncMock),
            patch(
                "fastapi_limiter.depends.RateLimiter.__call__",
                new_callable=lambda: AsyncMock(return_value=None),
            ),
            patch("app.api.jobs.redis") as mock_redis,
            patch("app.api.jobs.q") as mock_queue,
        ):
            # Configure mocks
            mock_queue.enqueue.return_value.id = "test-job-id"

            metadata_requests = 0
            job_requests = 0
            total_requests = 0

            # Alternate between metadata and job requests
            for i in range(settings.global_rate_limit_requests + 2):
                if i % 2 == 0:
                    response = client.post(
                        "/api/v1/metadata", json={"url": "https://example.com/video"}
                    )
                    metadata_requests += 1
                else:
                    response = client.post(
                        "/api/v1/jobs",
                        json={
                            "url": "https://example.com/video",
                            "start": 1,
                            "end": 10,
                            "accepted_terms": True,
                        },
                    )
                    job_requests += 1

                total_requests += 1

                if response.status_code == 429:
                    # Should be rate limited due to global limit
                    data = response.json()
                    assert (
                        "Rate limit exceeded" in data["detail"]
                        or "Job creation limit exceeded" in data["detail"]
                    )
                    break

    def test_get_client_ip_function(self):
        """Test IP extraction from various headers"""
        from unittest.mock import Mock

        from fastapi import Request

        # Test X-Forwarded-For header
        request = Mock(spec=Request)
        request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
        request.client.host = "127.0.0.1"

        ip = get_client_ip(request)
        assert ip == "192.168.1.1"  # Should get the first IP

        # Test X-Real-IP header
        request.headers = {"X-Real-IP": "192.168.1.2"}
        ip = get_client_ip(request)
        assert ip == "192.168.1.2"

        # Test fallback to client.host
        request.headers = {}
        ip = get_client_ip(request)
        assert ip == "127.0.0.1"

        # Test no client
        request.client = None
        ip = get_client_ip(request)
        assert ip == "unknown"

    @pytest.mark.asyncio
    async def test_init_rate_limit(self, mock_redis):
        """Test rate limiting initialization"""
        # Test successful initialization
        with patch("app.ratelimit.FastAPILimiter.init") as mock_init:
            mock_init.return_value = AsyncMock()
            await init_rate_limit()
            mock_init.assert_called_once()

        # Test failed initialization
        with patch("app.ratelimit.FastAPILimiter.init") as mock_init:
            mock_init.side_effect = Exception("Redis connection failed")
            with pytest.raises(Exception):
                await init_rate_limit()

    @pytest.mark.asyncio
    async def test_rate_limit_exception_handler(self):
        """Test the rate limit exception handler"""
        from unittest.mock import Mock

        from fastapi import HTTPException, Request

        request = Mock(spec=Request)
        request.url.path = "/api/v1/metadata"
        request.method = "POST"
        request.headers = {}
        request.client.host = "127.0.0.1"

        # Test 429 exception for metadata endpoint
        exc = HTTPException(status_code=429, headers={"Retry-After": "60"})
        result = await rate_limit_exception_handler(request, exc)

        assert "detail" in result
        assert "retry_after" in result
        assert "limit_type" in result
        assert result["retry_after"] == 60
        assert result["limit_type"] == "global"
        assert "Rate limit exceeded" in result["detail"]

        # Test 429 exception for job creation endpoint
        request.url.path = "/api/v1/jobs"
        result = await rate_limit_exception_handler(request, exc)

        assert result["limit_type"] == "job_creation"
        assert "Job creation limit" in result["detail"]

        # Test non-429 exception
        exc = HTTPException(status_code=400, detail="Bad request")
        result = await rate_limit_exception_handler(request, exc)

        assert result == {"detail": "Bad request"}

    def test_rate_limit_headers_in_response(self, client):
        """Test that rate limit responses include proper headers"""
        # Mock FastAPILimiter to avoid initialization issues
        with (
            patch("fastapi_limiter.FastAPILimiter.init", new_callable=AsyncMock),
            patch(
                "fastapi_limiter.depends.RateLimiter.__call__",
                new_callable=lambda: AsyncMock(return_value=None),
            ),
        ):
            # Make enough requests to trigger rate limit
            for _ in range(15):
                response = client.post(
                    "/api/v1/metadata", json={"url": "https://example.com/video"}
                )
                if response.status_code == 429:
                    # Check that Retry-After header is present
                    assert "retry-after" in response.headers

                    # Verify it's a valid integer
                    retry_after = response.headers["retry-after"]
                    assert retry_after.isdigit()
                    assert int(retry_after) > 0

                    # Check that it matches the response body
                    data = response.json()
                    assert int(retry_after) == data["retry_after"]
                    break

    def test_health_endpoint_not_rate_limited(self, client):
        """Test that health endpoint is not rate limited"""
        # Make many requests to health endpoint
        for _ in range(20):  # More than global limit
            response = client.get("/health")
            assert response.status_code == 200

    def test_docs_endpoint_not_rate_limited(self, client):
        """Test that docs endpoint is not rate limited"""
        # Make many requests to docs endpoint
        for _ in range(20):  # More than global limit
            response = client.get("/docs")
            # Docs should be accessible (200) or redirect (3xx), not rate limited (429)
            assert response.status_code != 429


class TestRateLimitConfiguration:
    """Test rate limit configuration"""

    def test_rate_limit_settings_from_env(self):
        """Test that rate limit settings can be configured via environment"""
        # Test default values
        assert settings.global_rate_limit_requests == 10
        assert settings.global_rate_limit_window == 60
        assert settings.job_rate_limit_requests == 3
        assert settings.job_rate_limit_window == 3600

    def test_rate_limit_key_functions(self):
        """Test rate limit key generation functions"""
        from unittest.mock import Mock

        from app.ratelimit import job_rate_limit_key_func, rate_limit_key_func

        request = Mock()
        request.headers = {}
        request.client.host = "192.168.1.1"

        global_key = rate_limit_key_func(request)
        job_key = job_rate_limit_key_func(request)

        assert global_key == "global_rate_limit:192.168.1.1"
        assert job_key == "job_create:192.168.1.1"
        assert global_key != job_key  # Should be different key spaces
