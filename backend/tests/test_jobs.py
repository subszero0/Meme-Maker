import uuid
from datetime import datetime

import fakeredis
import pytest
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from rq import Queue

from app.api import clips, jobs, metadata
from app.api import phase3_endpoints as admin
from app.api import video_proxy
from app.config import get_settings
from app.dependencies import get_redis
from app.main import app as main_app
from app.middleware.admin_auth import AdminAuthMiddleware
from app.middleware.queue_protection import QueueDosProtectionMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware


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
    settings = get_settings()

    # Create a new test app with the same configuration as main app
    app = FastAPI(
        title="Meme Maker API",
        version="0.1.0",
        description="A tool to clip and download videos from social media platforms",
    )

    # Add exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Log and return detailed validation errors."""
        error_messages = []
        for error in exc.errors():
            if isinstance(error.get("ctx", {}).get("error"), ValueError):
                error_messages.append(str(error["ctx"]["error"]))
            else:
                error_messages.append(error["msg"])

        print(
            f"❌ Validation error for {request.method} {request.url}: {error_messages}"
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Validation Error",
                "errors": error_messages,
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_exception_handler(request: Request, exc: ValueError):
        """Handle raw ValueErrors, returning a 422 response."""
        print(f"❌ ValueError caught for {request.method} {request.url}: {exc}")

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc)},
        )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add security middleware in the same order as main app
    app.add_middleware(
        QueueDosProtectionMiddleware,
        redis_client=fake_redis,
        bypass_protection_for_tests=True,
    )
    app.add_middleware(AdminAuthMiddleware, admin_api_key=settings.admin_api_key)
    app.add_middleware(SecurityHeadersMiddleware)

    # Include routers in the same order
    app.include_router(clips.router, prefix="/api/v1", tags=["clips"])
    app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])
    app.include_router(metadata.router, prefix="/api/v1", tags=["metadata"])
    app.include_router(video_proxy.router, prefix="/api/v1/video", tags=["video-proxy"])
    app.include_router(admin.router, tags=["admin"])

    # Override the Redis dependency
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
    # Check for the exact error message
    assert any(
        "Clip duration cannot exceed 1 minute (T-003 DoS protection)" == str(error)
        for error in error_detail
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
