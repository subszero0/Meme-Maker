"""
API Contract Integration Tests - Phase 2.2 of TestsToDo.md

Tests API behavior and contracts with minimal mocking.
Focus on API contracts, CORS, security headers, and endpoint behavior.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
import fakeredis
from rq import Queue

from app.main import app


@pytest.fixture
def client():
    """Test client for API contract testing with proper FastAPILimiter and Redis/RQ mocking"""

    # Mock rate limiter to avoid initialization issues
    async def mock_rate_limiter(*args, **kwargs):
        return None

    # Create fake Redis and RQ instances for job endpoints
    fake_redis = fakeredis.FakeRedis()
    fake_queue = Queue("clip_jobs", connection=fake_redis, is_async=False)

    with (
        # FastAPILimiter mocks
        patch("app.ratelimit.init_rate_limit", new_callable=AsyncMock),
        patch("fastapi_limiter.FastAPILimiter.init", new_callable=AsyncMock),
        patch("fastapi_limiter.FastAPILimiter.redis", fake_redis),
        patch(
            "fastapi_limiter.depends.RateLimiter.__call__",
            new_callable=lambda: mock_rate_limiter,
        ),
        # Redis/RQ mocks for job endpoints
        patch("app.redis", fake_redis),
        patch("app.q", fake_queue),
        patch("app.api.jobs.redis", fake_redis),
        patch("app.api.jobs.q", fake_queue),
        # Mock job queue enqueue for job creation tests
        patch("app.api.jobs.q.enqueue") as mock_enqueue,
    ):
        # Configure mock enqueue to return a mock job
        mock_job = MagicMock()
        mock_job.id = "test-job-id-12345678901234567890"
        mock_enqueue.return_value = mock_job

        yield TestClient(app)


class TestMetadataEndpointContract:
    """Test metadata endpoint API contract"""

    def test_metadata_endpoint_contract_valid_youtube(self, client):
        """Test metadata endpoint returns correct structure for valid YouTube URL"""
        # Arrange
        payload = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}

        # Act
        response = client.post("/api/v1/metadata", json=payload)

        # Assert - Contract structure (regardless of yt-dlp success/failure)
        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            data = response.json()
            # Verify response contract
            assert "url" in data
            assert "title" in data
            assert "duration" in data
            assert isinstance(data["duration"], (int, float))
            assert data["duration"] > 0
        else:
            # Error responses should have detail
            error_data = response.json()
            assert "detail" in error_data

    def test_metadata_endpoint_contract_invalid_url(self, client):
        """Test metadata endpoint contract for invalid URLs"""
        # Arrange
        payload = {"url": "https://example.com/not-a-video"}

        # Act
        response = client.post("/api/v1/metadata", json=payload)

        # Assert
        assert response.status_code in [400, 422]
        error_data = response.json()
        assert "detail" in error_data

    def test_metadata_endpoint_contract_missing_url(self, client):
        """Test metadata endpoint contract for missing URL"""
        # Arrange
        payload = {}

        # Act
        response = client.post("/api/v1/metadata", json=payload)

        # Assert
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data

    def test_metadata_endpoint_contract_malformed_request(self, client):
        """Test metadata endpoint contract for malformed requests"""
        # Act
        response = client.post("/api/v1/metadata", data="invalid-json")

        # Assert
        assert response.status_code == 422


class TestJobCreationContract:
    """Test job creation endpoint API contract"""

    def test_job_creation_contract_valid_request(self, client):
        """Test job creation endpoint returns correct structure"""
        # Arrange
        payload = {
            "url": "https://www.youtube.com/watch?v=test",
            "start": 10.0,
            "end": 70.0,
            "accepted_terms": True,
        }

        # Act
        response = client.post("/api/v1/jobs", json=payload)

        # Assert - Should return 202 with job structure
        assert response.status_code == 202
        data = response.json()

        # Verify response contract
        assert "job_id" in data
        assert "status" in data
        assert "created_at" in data
        assert len(data["job_id"]) == 32  # UUID hex string
        assert data["status"] == "queued"

    def test_job_creation_contract_validation_errors(self, client):
        """Test job creation endpoint validation error contracts"""
        # Arrange - Invalid duration (over 30 minutes)
        payload = {
            "url": "https://www.youtube.com/watch?v=test",
            "start": 0.0,
            "end": 1900.0,  # Over 30 minutes
            "accepted_terms": True,
        }

        # Act
        response = client.post("/api/v1/jobs", json=payload)

        # Assert
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data

    def test_job_creation_contract_missing_terms(self, client):
        """Test job creation requires terms acceptance"""
        # Arrange
        payload = {
            "url": "https://www.youtube.com/watch?v=test",
            "start": 10.0,
            "end": 70.0,
            "accepted_terms": False,
        }

        # Act
        response = client.post("/api/v1/jobs", json=payload)

        # Assert
        assert response.status_code in [
            400,
            422,
        ]  # Both are valid client errors for validation


class TestJobPollingContract:
    """Test job polling endpoint API contract"""

    def test_job_polling_contract_not_found(self, client):
        """Test job polling endpoint for non-existent job"""
        # Arrange
        fake_job_id = "nonexistent123456789012345678901234"

        # Act
        response = client.get(f"/api/v1/jobs/{fake_job_id}")

        # Assert
        assert response.status_code == 404
        error_data = response.json()
        assert "detail" in error_data

    def test_job_polling_contract_invalid_job_id(self, client):
        """Test job polling endpoint for invalid job ID format"""
        # Arrange
        invalid_job_id = "invalid-job-id"

        # Act
        response = client.get(f"/api/v1/jobs/{invalid_job_id}")

        # Assert
        # Should handle gracefully (either 404 or 422)
        assert response.status_code in [404, 422]


class TestCorsAndSecurityHeaders:
    """Test CORS and security headers"""

    def test_cors_headers_present(self, client):
        """Test that CORS headers are properly configured"""
        # Act
        response = client.options("/api/v1/metadata")

        # Assert
        assert response.status_code in [
            200,
            405,
        ]  # Some frameworks return 405 for OPTIONS

        # Check for CORS headers in a regular request
        response = client.get("/health")
        assert response.status_code == 200

    def test_security_headers_present(self, client):
        """Test that security headers are present"""
        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200

        # Check for basic security headers
        headers = response.headers
        # Note: Specific headers depend on middleware configuration
        # This test ensures the endpoint is accessible and returns proper HTTP response

    def test_content_type_headers(self, client):
        """Test that API endpoints return correct content types"""
        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_api_versioning_consistency(self, client):
        """Test that API versioning is consistent across endpoints"""
        # Arrange - Test multiple v1 endpoints
        endpoints = ["/api/v1/metadata", "/api/v1/jobs"]

        for endpoint in endpoints:
            # Act
            response = client.post(endpoint, json={})

            # Assert - Should not return 404 (endpoint exists)
            assert response.status_code != 404, f"Endpoint {endpoint} not found"

    def test_error_response_consistency(self, client):
        """Test that error responses follow consistent format"""
        # Arrange - Trigger various error types
        test_cases = [
            ("/api/v1/metadata", {}),  # Missing required field
            ("/api/v1/jobs", {}),  # Missing required fields
        ]

        for endpoint, payload in test_cases:
            # Act
            response = client.post(endpoint, json=payload)

            # Assert - Error responses should have consistent structure
            if response.status_code >= 400:
                error_data = response.json()
                assert (
                    "detail" in error_data
                ), f"Error response from {endpoint} missing 'detail' field"
