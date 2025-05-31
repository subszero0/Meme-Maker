import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import fakeredis
from fastapi.testclient import TestClient
from rq import Queue

# Mock the storage manager before importing the app
with patch('app.utils.storage.StorageManager') as mock_storage_class:
    mock_storage_instance = MagicMock()
    mock_storage_class.return_value = mock_storage_instance
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
    with patch('app.redis', fake_redis), \
         patch('app.q', fake_queue), \
         patch('app.api.jobs.redis', fake_redis), \
         patch('app.api.jobs.q', fake_queue), \
         patch('app.ratelimit.init_rate_limit', new_callable=AsyncMock), \
         patch('app.api.jobs.global_limiter', return_value=None), \
         patch('app.api.jobs.job_creation_limiter', return_value=None):
        yield TestClient(app)


def test_create_job_without_accepted_terms(client_with_fake_redis):
    """Test that job creation fails when accepted_terms is False"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "start": "00:00:10",
        "end": "00:00:30",
        "accepted_terms": False
    }
    
    response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)
    
    assert response.status_code == 400
    assert response.json()["detail"] == "You must accept the Terms of Use to proceed."


def test_create_job_missing_accepted_terms(client_with_fake_redis):
    """Test that job creation fails when accepted_terms field is missing"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "start": "00:00:10",
        "end": "00:00:30"
        # missing accepted_terms field
    }
    
    response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)
    
    assert response.status_code == 422  # Unprocessable Entity for missing required field
    error_detail = response.json()["detail"]
    
    # Check that the validation error mentions the missing field
    assert any("accepted_terms" in str(error).lower() for error in error_detail)


def test_create_job_with_accepted_terms(client_with_fake_redis):
    """Test that job creation succeeds when accepted_terms is True"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "start": "00:00:10",
        "end": "00:00:30",
        "accepted_terms": True
    }
    
    with patch('app.api.jobs.q.enqueue') as mock_enqueue:
        mock_enqueue.return_value = MagicMock()
        
        response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)
        
        assert response.status_code == 202  # Accepted
        data = response.json()
        assert "job_id" in data
        assert len(data["job_id"]) == 32  # UUID hex string
        assert data["status"] == "queued"
        assert "created_at" in data
        
        # Verify job was enqueued
        mock_enqueue.assert_called_once()


def test_job_create_with_invalid_time_format(client_with_fake_redis):
    """Test that job creation fails with invalid time format"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "start": "invalid_time",
        "end": "00:00:30",
        "accepted_terms": True
    }
    
    response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)
    
    assert response.status_code == 422
    assert "Invalid time format" in response.json()["detail"]


def test_job_create_with_duration_too_long(client_with_fake_redis):
    """Test that job creation fails when duration exceeds 3 minutes"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "start": "00:00:00",
        "end": "00:03:01",  # 3 minutes 1 second
        "accepted_terms": True
    }
    
    response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)
    
    assert response.status_code == 422
    assert "Clip duration cannot exceed 180 seconds (3 minutes)" in response.json()["detail"]


def test_job_create_with_end_before_start(client_with_fake_redis):
    """Test that job creation fails when end time is before start time"""
    job_data = {
        "url": "https://www.youtube.com/watch?v=test",
        "start": "00:00:30",
        "end": "00:00:10",  # end before start
        "accepted_terms": True
    }
    
    response = client_with_fake_redis.post("/api/v1/jobs", json=job_data)
    
    assert response.status_code == 422
    assert "end time must be greater than start time" in response.json()["detail"] 