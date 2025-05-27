import pytest
import uuid
from decimal import Decimal
from datetime import datetime
from unittest.mock import patch, MagicMock

import fakeredis
from fastapi.testclient import TestClient
from rq import Queue

from app.main import app
from app.models import JobStatus


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
    with patch('app.redis', fake_redis), \
         patch('app.q', fake_queue), \
         patch('app.api.jobs.redis', fake_redis), \
         patch('app.api.jobs.q', fake_queue):
        yield TestClient(app)


def test_create_job_valid(client_with_fake_redis):
    """Test creating a valid job returns 201 and enqueues job"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "in_ts": 10.0,
        "out_ts": 70.0
    }
    
    with patch('app.api.jobs.q.enqueue') as mock_enqueue:
        mock_enqueue.return_value = MagicMock()
        
        response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert len(data["id"]) == 32  # UUID hex string
        assert data["status"] == "queued"
        assert "created_at" in data
        
        # Verify job was enqueued
        mock_enqueue.assert_called_once()
        args = mock_enqueue.call_args[0]
        assert args[0] == "worker.process_clip.process_clip"
        assert args[1] == data["id"]  # job_id is first parameter now
        assert args[2] == "https://www.youtube.com/watch?v=test"
        assert args[3] == 10.0
        assert args[4] == 70.0


def test_create_job_duration_too_long(client_with_fake_redis):
    """Test that jobs over 180 seconds are rejected with 422"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "in_ts": 10.0,
        "out_ts": 200.0  # 190 seconds > 180
    }
    
    response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)
    
    assert response.status_code == 422
    assert "180 seconds" in response.json()["detail"]


def test_create_job_invalid_duration(client_with_fake_redis):
    """Test that jobs with out_ts <= in_ts are rejected"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "in_ts": 70.0,
        "out_ts": 60.0  # out_ts < in_ts
    }
    
    response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)
    
    assert response.status_code == 422
    assert "out_ts must be greater than in_ts" in response.json()["detail"]


def test_create_job_enqueue_failure(client_with_fake_redis, fake_redis):
    """Test that enqueue failure cleans up job from Redis"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "in_ts": 10.0,
        "out_ts": 70.0
    }
    
    with patch('app.api.jobs.q.enqueue') as mock_enqueue:
        mock_enqueue.side_effect = Exception("Queue error")
        
        response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)
        
        assert response.status_code == 500
        assert "Failed to enqueue job" in response.json()["detail"]
        
        # Verify no job data remains in Redis
        job_keys = fake_redis.keys("job:*")
        assert len(job_keys) == 0


def test_get_job_queued_status(client_with_fake_redis, fake_redis):
    """Test polling returns queued status correctly"""
    # Manually create a job in Redis
    job_id = uuid.uuid4().hex
    job_data = {
        "id": job_id,
        "url": "https://www.youtube.com/watch?v=test",
        "in_ts": "10.0",
        "out_ts": "70.0",
        "status": "queued",
        "progress": "None",
        "error_code": "None",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    fake_redis.hset(f"job:{job_id}", mapping=job_data)
    
    response = client_with_fake_redis.get(f"/api/v1/jobs/{job_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["status"] == "queued"
    assert data["progress"] is None
    assert "url" not in data or data["url"] is None


def test_get_job_working_status(client_with_fake_redis, fake_redis):
    """Test polling returns working status with progress"""
    job_id = uuid.uuid4().hex
    job_data = {
        "id": job_id,
        "url": "https://www.youtube.com/watch?v=test",
        "in_ts": "10.0",
        "out_ts": "70.0",
        "status": "working",
        "progress": "45",
        "error_code": "None",
        "created_at": datetime.utcnow().isoformat() + "Z"
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
    job_id = uuid.uuid4().hex
    job_data = {
        "id": job_id,
        "url": "https://www.youtube.com/watch?v=test",
        "in_ts": "10.0",
        "out_ts": "70.0",
        "status": "done",
        "progress": "None",
        "error_code": "None",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "url": "https://s3.amazonaws.com/bucket/file.mp4?presigned=true"
    }
    
    fake_redis.hset(f"job:{job_id}", mapping=job_data)
    
    response = client_with_fake_redis.get(f"/api/v1/jobs/{job_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["status"] == "done"
    assert data["url"] == "https://s3.amazonaws.com/bucket/file.mp4?presigned=true"
    
    # Check that TTL was set (fakeredis supports TTL)
    ttl = fake_redis.ttl(f"job:{job_id}")
    assert ttl > 0 and ttl <= 3600


def test_get_job_error_status(client_with_fake_redis, fake_redis):
    """Test polling returns error status with error code and sets TTL"""
    job_id = uuid.uuid4().hex
    job_data = {
        "id": job_id,
        "url": "https://www.youtube.com/watch?v=test",
        "in_ts": "10.0",
        "out_ts": "70.0",
        "status": "error",
        "progress": "None",
        "error_code": "DOWNLOAD_FAILED",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    fake_redis.hset(f"job:{job_id}", mapping=job_data)
    
    response = client_with_fake_redis.get(f"/api/v1/jobs/{job_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["status"] == "error"
    assert data["error_code"] == "DOWNLOAD_FAILED"
    
    # Check that TTL was set
    ttl = fake_redis.ttl(f"job:{job_id}")
    assert ttl > 0 and ttl <= 3600


def test_get_job_not_found(client_with_fake_redis):
    """Test polling nonexistent job returns 404"""
    response = client_with_fake_redis.get("/api/v1/jobs/nonexistent-id")
    
    assert response.status_code == 404
    assert "Job not found" in response.json()["detail"] 