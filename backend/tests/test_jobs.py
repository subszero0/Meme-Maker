"""
Simplified job tests following TestsToDo.md recommendations.
Consolidates 23 tests into 5 focused tests following good testing practices:
- Arrange-Act-Assert structure
- Descriptive names
- Single responsibility
- Minimal mocking
- Business value focus
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import fakeredis
import pytest
from fastapi.testclient import TestClient
from rq import Queue

from app.main import app


@pytest.fixture
def fake_redis():
    """Fixture to provide a fake Redis instance"""
    return fakeredis.FakeRedis()


@pytest.fixture
def fake_queue(fake_redis):
    """Fixture to provide a fake RQ queue"""
    return Queue("clips", connection=fake_redis, is_async=False)


@pytest.fixture
def client_with_fake_redis(fake_redis, fake_queue):
    """Test client with mocked Redis and RQ"""

    async def mock_rate_limiter(*args, **kwargs):
        return None

    with (
        patch("app.redis", fake_redis),
        patch("app.q", fake_queue),
        patch("app.api.jobs.redis", fake_redis),
        patch("app.api.jobs.q", fake_queue),
        patch("app.ratelimit.init_rate_limit", new_callable=AsyncMock),
        patch("fastapi_limiter.FastAPILimiter.redis", fake_redis),
        patch(
            "fastapi_limiter.depends.RateLimiter.__call__",
            new_callable=lambda: mock_rate_limiter,
        ),
    ):
        yield TestClient(app)


def test_create_job_happy_path(client_with_fake_redis):
    """Test creating a valid job returns 202 and enqueues job correctly"""
    # Arrange
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "start": 10.0,
        "end": 70.0,
        "accepted_terms": True,
    }

    # Act & Assert
    with patch("app.api.jobs.q.enqueue") as mock_enqueue:
        mock_enqueue.return_value = MagicMock()

        response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)

        # Assert response structure
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert len(data["job_id"]) == 32  # UUID hex string
        assert data["status"] == "queued"
        assert "created_at" in data

        # Assert job was enqueued with correct parameters
        mock_enqueue.assert_called_once()
        args = mock_enqueue.call_args[0]
        assert args[0] == "clip_processor.process_clip"
        assert args[1] == data["job_id"]
        assert args[2] == "https://www.youtube.com/watch?v=test"
        assert args[3] == 10.0
        assert args[4] == 70.0


@pytest.mark.parametrize(
    "invalid_data,expected_error",
    [
        # Invalid time format
        (
            {
                "start": "10",
                "end": "70.0",
                "url": "https://youtube.com/watch?v=test",
                "accepted_terms": True,
            },
            "Time must be in mm:ss format",
        ),
        # Invalid time values
        (
            {
                "start": "00:abc",
                "end": "01:30",
                "url": "https://youtube.com/watch?v=test",
                "accepted_terms": True,
            },
            "Invalid time format",
        ),
        # Duration too long (over 30 minutes)
        (
            {
                "start": 10.0,
                "end": 1900.0,
                "url": "https://youtube.com/watch?v=test",
                "accepted_terms": True,
            },
            "Clip too long",
        ),
        # End before start
        (
            {
                "start": 70.0,
                "end": 10.0,
                "url": "https://youtube.com/watch?v=test",
                "accepted_terms": True,
            },
            "end time must be greater than start time",
        ),
        # Missing accepted terms
        (
            {"start": 10.0, "end": 70.0, "url": "https://youtube.com/watch?v=test"},
            "accepted_terms",
        ),
        # Terms not accepted
        (
            {
                "start": 10.0,
                "end": 70.0,
                "url": "https://youtube.com/watch?v=test",
                "accepted_terms": False,
            },
            "You must accept the Terms of Use to proceed",
        ),
    ],
)
def test_create_job_validation_errors(
    client_with_fake_redis, invalid_data, expected_error
):
    """Test various job creation validation scenarios return 422 with
    appropriate errors"""
    # Act
    response = client_with_fake_redis.post("/api/v1/jobs", json=invalid_data)

    # Assert
    assert response.status_code in [
        400,
        422,
    ]  # Both are valid client errors for validation
    assert expected_error in str(response.json())


@pytest.mark.parametrize(
    "job_status,expected_response",
    [
        # Queued status
        ("queued", {"status": "queued", "progress": None}),
        # Working status with progress
        ("working", {"status": "working", "progress": 45}),
        # Done status with download URL
        (
            "done",
            {
                "status": "done",
                "progress": 100,
                "url": "https://s3.example.com/test.mp4",
            },
        ),
        # Error status with error details
        (
            "error",
            {
                "status": "error",
                "error_code": "YTDLP_FAIL",
                "error_message": "Video not found",
            },
        ),
    ],
)
def test_get_job_status(
    client_with_fake_redis, fake_redis, job_status, expected_response
):
    """Test retrieving job status for different job states"""
    # Arrange
    job_id = uuid.uuid4().hex
    job_data = {
        "id": job_id,
        "url": "https://www.youtube.com/watch?v=test",
        "in_ts": "10.0",
        "out_ts": "70.0",
        "status": job_status,
        "created_at": datetime.utcnow().isoformat() + "Z",
        **expected_response,
    }

    # For done status, add object_key and mock presigned URL generation
    expected_download_url = None
    if job_status == "done" and "url" in expected_response:
        job_data["object_key"] = "test-clip.mp4"
        # Keep the original URL field for Job model validation
        # just store the expected URL separately for later comparison
        expected_download_url = expected_response["url"]

    # Filter out None values as Redis doesn't accept them
    job_data = {k: v for k, v in job_data.items() if v is not None}

    # Mock presigned URL generation for done jobs
    with patch("app.api.jobs.get_storage") as mock_get_storage:
        if job_status == "done" and "object_key" in job_data:
            mock_storage = MagicMock()
            mock_storage.generate_presigned_url.return_value = expected_download_url
            mock_get_storage.return_value = mock_storage

        fake_redis.hset(f"job:{job_id}", mapping=job_data)

        # Act
        response = client_with_fake_redis.get(f"/api/v1/jobs/{job_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["status"] == job_status

        # Assert specific status fields
        if "progress" in expected_response:
            if expected_response["progress"] is not None:
                assert data["progress"] == expected_response["progress"]
        if "url" in expected_response:
            if job_status == "done":
                # For done jobs, compare with the expected download URL
                assert data["link"] == expected_download_url
            else:
                assert data["link"] == expected_response["url"]
        if "error_code" in expected_response:
            assert data["error_code"] == expected_response["error_code"]


def test_job_completion_flow(client_with_fake_redis, fake_redis):
    """Test complete job lifecycle from creation to completion"""
    # Arrange - Create job
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "start": 10.0,
        "end": 70.0,
        "accepted_terms": True,
    }

    with patch("app.api.jobs.q.enqueue") as mock_enqueue:
        mock_enqueue.return_value = MagicMock()

        # Act - Create job
        create_response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)
        assert create_response.status_code == 202
        job_id = create_response.json()["job_id"]

        # Simulate job processing by updating Redis directly
        # (This simulates what the worker would do)

        # 1. Job starts working
        fake_redis.hset(f"job:{job_id}", mapping={"status": "working", "progress": 50})

        # Act - Check working status
        status_response = client_with_fake_redis.get(f"/api/v1/jobs/{job_id}")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "working"
        assert status_response.json()["progress"] == 50

        # 2. Job completes
        fake_redis.hset(
            f"job:{job_id}",
            mapping={
                "status": "done",
                "progress": 100,
                # Add object_key for presigned URL generation
                "object_key": "test-clip.mp4",
            },
        )

        # Mock presigned URL generation for the completion status check
        with patch("app.api.jobs.get_storage") as mock_get_storage:
            mock_storage = MagicMock()
            mock_storage.generate_presigned_url.return_value = (
                "https://s3.example.com/clip.mp4"
            )
            mock_get_storage.return_value = mock_storage

            # Act - Check completion status
            final_response = client_with_fake_redis.get(f"/api/v1/jobs/{job_id}")
            assert final_response.status_code == 200
            final_data = final_response.json()
            assert final_data["status"] == "done"
            assert final_data["progress"] == 100
            assert final_data["link"] == "https://s3.example.com/clip.mp4"


def test_rate_limiting():
    """Test that rate limiting configuration is properly enabled"""
    # This is a simple test to ensure rate limiting is configured
    # Real rate limiting testing would require integration tests
    from app.config import settings

    # Assert rate limiting is configured
    assert settings.global_rate_limit_requests > 0
    assert settings.max_jobs_per_hour > 0
    assert isinstance(settings.global_rate_limit_requests, int)
    assert isinstance(settings.max_jobs_per_hour, int)


def test_job_not_found(client_with_fake_redis):
    """Test that requesting non-existent job returns 404"""
    # Arrange
    non_existent_job_id = uuid.uuid4().hex

    # Act
    response = client_with_fake_redis.get(f"/api/v1/jobs/{non_existent_job_id}")

    # Assert
    assert response.status_code == 404
    assert "not found" in str(response.json()).lower()
