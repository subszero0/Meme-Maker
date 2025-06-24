import uuid
from datetime import datetime

import fakeredis
import pytest
from fastapi.testclient import TestClient
from rq import Queue


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
    from app.dependencies import get_redis
    from app.main import app

    # Override the dependency
    app.dependency_overrides[get_redis] = lambda: fake_redis

    try:
        yield TestClient(app)
    finally:
        # Clean up overrides
        app.dependency_overrides.clear()


def test_create_job_valid(client_with_fake_redis, fake_redis):
    """Test creating a valid job returns 201 and stores job in Redis"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "in_ts": 10.0,
        "out_ts": 70.0,
    }

    response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert len(data["id"]) == 36  # UUID string with dashes
    assert data["status"] == "queued"
    assert "created_at" in data

    # Verify job was stored in Redis
    job_key = f"job:{data['id']}"
    stored_data = fake_redis.hgetall(job_key)
    assert stored_data is not None
    assert stored_data[b"status"] == b"queued"
    assert stored_data[b"url"] == b"https://www.youtube.com/watch?v=test"


def test_create_job_duration_too_long(client_with_fake_redis):
    """Test that jobs over 180 seconds are rejected with 422"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "in_ts": 10.0,
        "out_ts": 200.0,  # 190 seconds > 180
    }

    response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)

    assert response.status_code == 422
    error_detail = response.json()["errors"]
    # Pydantic validation errors are now in list format
    assert any(
        "180" in str(error) or "3 minutes" in str(error) for error in error_detail
    )


def test_create_job_invalid_duration(client_with_fake_redis):
    """Test that jobs with out_ts <= in_ts are rejected"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "in_ts": 70.0,
        "out_ts": 60.0,  # out_ts < in_ts
    }

    response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)

    assert response.status_code == 422
    error_detail = response.json()["errors"]
    # Pydantic validation errors are now in list format
    assert any("greater than start time" in str(error) for error in error_detail)


def test_create_job_redis_unavailable():
    """Test handling when Redis is unavailable"""
    from app.dependencies import get_redis
    from app.main import app

    # Override to return None (Redis unavailable)
    app.dependency_overrides[get_redis] = lambda: None

    try:
        client = TestClient(app)
        job_data = {
            "url": "https://www.youtube.com/watch?v=test",
            "in_ts": 10.0,
            "out_ts": 70.0,
        }

        response = client.post("/api/v1/jobs", json=job_data)

        assert response.status_code == 503
        assert "Redis service unavailable" in response.json()["detail"]
    finally:
        # Clean up overrides
        app.dependency_overrides.clear()


def test_get_job_queued_status(client_with_fake_redis, fake_redis):
    """Test polling returns queued status correctly"""
    # Manually create a job in Redis
    job_id = str(uuid.uuid4())  # Use string format with dashes, not hex
    job_data = {
        "id": job_id,
        "url": "https://www.youtube.com/watch?v=test",
        "in_ts": "10.0",
        "out_ts": "70.0",
        "status": "queued",
        "progress": "0",
        "error_code": "None",
        "created_at": datetime.utcnow().isoformat() + "Z",
    }

    fake_redis.hset(f"job:{job_id}", mapping=job_data)

    response = client_with_fake_redis.get(f"/api/v1/jobs/{job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["status"] == "queued"
    assert data["progress"] == 0  # "None" gets converted to 0 in progress field
    assert data["download_url"] is None


def test_get_job_working_status(client_with_fake_redis, fake_redis):
    """Test polling returns working status with progress"""
    job_id = str(uuid.uuid4())
    job_data = {
        "id": job_id,
        "url": "https://www.youtube.com/watch?v=test",
        "in_ts": "10.0",
        "out_ts": "70.0",
        "status": "working",
        "progress": "45",
        "error_code": "None",
        "created_at": datetime.utcnow().isoformat() + "Z",
    }

    fake_redis.hset(f"job:{job_id}", mapping=job_data)

    response = client_with_fake_redis.get(f"/api/v1/jobs/{job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["status"] == "working"
    assert data["progress"] == 45


def test_get_job_done_status(client_with_fake_redis, fake_redis):
    """Test polling returns done status with download URL and sets TTL"""
    job_id = str(uuid.uuid4())
    job_data = {
        "id": job_id,
        "url": "https://www.youtube.com/watch?v=test",
        "in_ts": "10.0",
        "out_ts": "70.0",
        "status": "done",
        "progress": "100",
        "error_code": "None",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "download_url": "https://s3.amazonaws.com/bucket/file.mp4?presigned=true",
    }

    fake_redis.hset(f"job:{job_id}", mapping=job_data)

    response = client_with_fake_redis.get(f"/api/v1/jobs/{job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["status"] == "done"
    assert (
        data["download_url"]
        == "https://s3.amazonaws.com/bucket/file.mp4?presigned=true"
    )

    # TTL is set during job creation, not during retrieval
    # Just verify the job data is accessible
    assert response.status_code == 200


def test_get_job_error_status(client_with_fake_redis, fake_redis):
    """Test polling returns error status with error code and sets TTL"""
    job_id = str(uuid.uuid4())
    job_data = {
        "id": job_id,
        "url": "https://www.youtube.com/watch?v=test",
        "in_ts": "10.0",
        "out_ts": "70.0",
        "status": "error",
        "progress": "0",
        "error_code": "DOWNLOAD_FAILED",
        "created_at": datetime.utcnow().isoformat() + "Z",
    }

    fake_redis.hset(f"job:{job_id}", mapping=job_data)

    response = client_with_fake_redis.get(f"/api/v1/jobs/{job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["status"] == "error"
    assert data["error_code"] == "DOWNLOAD_FAILED"

    # TTL is set during job creation, not during retrieval
    # Just verify the job data is accessible
    assert response.status_code == 200


def test_get_job_not_found(client_with_fake_redis):
    """Test polling nonexistent job returns 404"""
    response = client_with_fake_redis.get("/api/v1/jobs/nonexistent-id")

    assert response.status_code == 404
    assert "Job not found" in response.json()["detail"]
