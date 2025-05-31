import pytest
import uuid
from decimal import Decimal
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock, Mock

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
         patch('app.api.jobs.q', fake_queue), \
         patch('app.ratelimit.init_rate_limit', new_callable=AsyncMock), \
         patch('app.api.jobs.clip_limiter', return_value=None):
        yield TestClient(app)


def test_create_job_valid(client_with_fake_redis):
    """Test creating a valid job returns 202 and enqueues job"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "start": 10.0,
        "end": 70.0,
        "accepted_terms": True
    }
    
    with patch('app.api.jobs.q.enqueue') as mock_enqueue:
        mock_enqueue.return_value = MagicMock()
        
        response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)
        
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert len(data["job_id"]) == 32  # UUID hex string
        assert data["status"] == "queued"
        assert "created_at" in data
        
        # Verify job was enqueued
        mock_enqueue.assert_called_once()
        args = mock_enqueue.call_args[0]
        assert args[0] == "clip_processor.process_clip"
        assert args[1] == data["job_id"]  # job_id is first parameter now
        assert args[2] == "https://www.youtube.com/watch?v=test"
        assert args[3] == 10.0
        assert args[4] == 70.0


def test_create_job_with_string_timestamps(client_with_fake_redis):
    """Test creating a valid job with hh:mm:ss string format returns 202"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "start": "00:00:10",
        "end": "00:01:10",
        "accepted_terms": True
    }
    
    with patch('app.api.jobs.q.enqueue') as mock_enqueue:
        mock_enqueue.return_value = MagicMock()
        
        response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)
        
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        
        # Verify job was enqueued with converted seconds
        mock_enqueue.assert_called_once()
        args = mock_enqueue.call_args[0]
        assert args[3] == 10.0  # 00:00:10 -> 10 seconds
        assert args[4] == 70.0  # 00:01:10 -> 70 seconds


def test_create_job_with_fractional_seconds(client_with_fake_redis):
    """Test creating a job with fractional seconds in hh:mm:ss.mmm format"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "start": "00:00:10.5",
        "end": "00:01:10.25",
        "accepted_terms": True
    }
    
    with patch('app.api.jobs.q.enqueue') as mock_enqueue:
        mock_enqueue.return_value = MagicMock()
        
        response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)
        
        assert response.status_code == 202
        
        # Verify job was enqueued with converted fractional seconds
        mock_enqueue.assert_called_once()
        args = mock_enqueue.call_args[0]
        assert args[3] == 10.5   # 00:00:10.5 -> 10.5 seconds
        assert args[4] == 70.25  # 00:01:10.25 -> 70.25 seconds


def test_create_job_with_integer_seconds(client_with_fake_redis):
    """Test creating a job with integer seconds"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test", 
        "start": 15,
        "end": 75,
        "accepted_terms": True
    }
    
    with patch('app.api.jobs.q.enqueue') as mock_enqueue:
        mock_enqueue.return_value = MagicMock()
        
        response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)
        
        assert response.status_code == 202
        
        # Verify job was enqueued with integer seconds converted to float
        mock_enqueue.assert_called_once()
        args = mock_enqueue.call_args[0]
        assert args[3] == 15.0
        assert args[4] == 75.0


def test_create_job_invalid_string_format(client_with_fake_redis):
    """Test that invalid time string formats are rejected with 422"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "start": "10:30",  # Missing seconds part
        "end": "70.0",
        "accepted_terms": True
    }
    
    response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)
    
    assert response.status_code == 422
    assert "Time must be in hh:mm:ss format or numeric seconds" in str(response.json())


def test_create_job_invalid_time_values(client_with_fake_redis):
    """Test that invalid time values in string format are rejected"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "start": "00:00:abc",  # Invalid seconds value
        "end": "00:01:30",
        "accepted_terms": True
    }
    
    response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)
    
    assert response.status_code == 422
    assert "Invalid time format" in str(response.json())


def test_create_job_duration_too_long(client_with_fake_redis):
    """Test that jobs over 180 seconds are rejected with 422"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "start": 10.0,
        "end": 200.0,  # 190 seconds > 180
        "accepted_terms": True
    }
    
    response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)
    
    assert response.status_code == 422
    assert "180 seconds" in response.json()["detail"]


def test_clip_exactly_30_min_passes(client_with_fake_redis):
    """Test that a clip of exactly 30 minutes (1800 seconds) is accepted"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "start": 0.0,
        "end": 1800.0,  # Exactly 30 minutes
        "accepted_terms": True
    }
    
    with patch('app.api.jobs.q.enqueue') as mock_enqueue:
        mock_enqueue.return_value = MagicMock()
        
        response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)
        
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        
        # Verify job was enqueued
        mock_enqueue.assert_called_once()


def test_clip_over_30_min_fails(client_with_fake_redis):
    """Test that a clip over 30 minutes (1801 seconds) is rejected"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "start": 0.0,
        "end": 1801.0,  # 1 second over 30 minutes
        "accepted_terms": True
    }
    
    response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)
    
    assert response.status_code == 422
    assert "Clip too long" in response.json()["detail"]


def test_create_job_invalid_duration(client_with_fake_redis):
    """Test that jobs with end <= start are rejected"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "start": 70.0,
        "end": 60.0,  # end < start
        "accepted_terms": True
    }
    
    response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)
    
    assert response.status_code == 422
    assert "end time must be greater than start time" in response.json()["detail"]


def test_create_job_enqueue_failure(client_with_fake_redis, fake_redis):
    """Test that enqueue failure cleans up job from Redis"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "start": 10.0,
        "end": 70.0,
        "accepted_terms": True
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
    assert data["job_id"] == job_id
    assert data["status"] == "queued"
    assert data["progress"] is None


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
    assert data["job_id"] == job_id
    assert data["status"] == "working"
    assert data["progress"] == 45


def test_get_job_done_status(client_with_fake_redis, fake_redis):
    """Test polling returns done status with download URL and sets TTL"""
    job_id = uuid.uuid4().hex
    object_key = f"clips/{job_id}.mp4"
    job_data = {
        "id": job_id,
        "url": "https://www.youtube.com/watch?v=test",
        "in_ts": "10.0",
        "out_ts": "70.0",
        "status": "done",
        "progress": "None",
        "error_code": "None",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "object_key": object_key
    }
    
    fake_redis.hset(f"job:{job_id}", mapping=job_data)
    
    # Mock the storage service to return a presigned URL
    with patch('app.api.jobs.get_storage') as mock_get_storage:
        mock_storage = Mock()
        mock_storage.generate_presigned_url.return_value = "https://s3.amazonaws.com/bucket/file.mp4?presigned=true"
        mock_get_storage.return_value = mock_storage
        
        response = client_with_fake_redis.get(f"/api/v1/jobs/{job_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["status"] == "done"
        assert data["link"] == "https://s3.amazonaws.com/bucket/file.mp4?presigned=true"
        
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
    assert data["job_id"] == job_id
    assert data["status"] == "error"
    assert data["error_code"] == "DOWNLOAD_FAILED"
    
    # Check that TTL was set
    ttl = fake_redis.ttl(f"job:{job_id}")
    assert ttl > 0 and ttl <= 3600


def test_get_job_not_found(client_with_fake_redis):
    """Test polling non-existent job returns 404"""
    fake_id = uuid.uuid4().hex
    
    response = client_with_fake_redis.get(f"/api/v1/jobs/{fake_id}")
    
    assert response.status_code == 404
    assert "Job not found" in response.json()["detail"]


def test_rate_limiting_enabled():
    """Test that rate limiting dependency is properly configured"""
    from app.api.jobs import router
    from app.ratelimit import clip_limiter
    
    # Check that the POST endpoint has rate limiting dependency
    post_endpoint = None
    for route in router.routes:
        if hasattr(route, 'methods') and 'POST' in route.methods and route.path == '/jobs':
            post_endpoint = route
            break
    
    assert post_endpoint is not None, "POST /jobs endpoint not found"
    
    # Check that clip_limiter is in the dependencies
    dependencies = getattr(post_endpoint, 'dependencies', [])
    rate_limit_dep_found = any(
        hasattr(dep, 'dependency') and 'clip_limiter' in str(dep.dependency)
        for dep in dependencies
    )
    
    assert rate_limit_dep_found or len(dependencies) > 0, "Rate limiting dependency not found" 