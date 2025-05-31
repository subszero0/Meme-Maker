"""
Tests for job creation and processing flow with mock storage.

This module tests the complete job flow from creation to download cleanup
using the InMemoryStorage mock to avoid hitting real S3/MinIO.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

import fakeredis
from fastapi.testclient import TestClient
from rq import Queue

from app.main import app
from app.models import JobStatus


@pytest.fixture
def fake_redis():
    """Fixture to provide a fake Redis instance for job tracking."""
    return fakeredis.FakeRedis()


@pytest.fixture
def fake_queue(fake_redis):
    """Fixture to provide a fake RQ queue for job processing."""
    return Queue("clips", connection=fake_redis, is_async=False)


@pytest.fixture
def client_with_mock_storage(fake_redis, fake_queue, mock_storage):
    """
    Test client with mocked Redis, RQ, and storage.
    
    Uses the mock_storage fixture from conftest.py which patches get_storage()
    to return an InMemoryStorage instance.
    """
    with patch('app.redis', fake_redis), \
         patch('app.q', fake_queue), \
         patch('app.api.jobs.redis', fake_redis), \
         patch('app.api.jobs.q', fake_queue), \
         patch('app.ratelimit.init_rate_limit', new_callable=AsyncMock), \
         patch('app.api.jobs.clip_limiter', return_value=None):
        yield TestClient(app)


class TestJobFlowWithMockStorage:
    """Test the complete job flow using in-memory storage."""
    
    def test_job_creation_with_mock_storage(self, client_with_mock_storage, mock_storage):
        """Test creating a job returns 202 and correct job_id."""
        job_data = {
            "url": "https://www.youtube.com/watch?v=BaW_jenozKc",
            "start_seconds": 5.0,
            "end_seconds": 15.0,
            "accepted_terms": True
        }
        
        with patch('app.api.jobs.q.enqueue') as mock_enqueue:
            mock_job = MagicMock()
            mock_job.id = "test-rq-job-id"
            mock_enqueue.return_value = mock_job
            
            response = client_with_mock_storage.post("/api/v1/jobs", json=job_data)
            
            # Assert job creation response
            assert response.status_code == 202, f"Expected 202, got {response.status_code}: {response.text}"
            data = response.json()
            assert "job_id" in data, "Response missing job_id field"
            job_id = data["job_id"]
            assert len(job_id) == 32, f"Expected 32-char UUID hex, got {len(job_id)} chars"
            assert data["status"] == "queued", f"Expected status 'queued', got '{data['status']}'"
            assert "created_at" in data, "Response missing created_at field"
            
            # Verify job was enqueued with correct parameters
            mock_enqueue.assert_called_once()
            args = mock_enqueue.call_args[0]
            assert args[0] == "clip_processor.process_clip", "Wrong function name enqueued"
            assert args[1] == job_id, "Wrong job_id passed to worker"
            assert args[2] == "https://www.youtube.com/watch?v=BaW_jenozKc", "Wrong URL passed"
            assert args[3] == 5.0, "Wrong start_seconds passed"
            assert args[4] == 15.0, "Wrong end_seconds passed"
    
    def test_worker_upload_simulation(self, client_with_mock_storage, mock_storage):
        """Test simulating worker uploading a file to mock storage."""
        # Create a job first
        job_data = {
            "url": "https://www.youtube.com/watch?v=BaW_jenozKc",
            "start_seconds": 5.0,
            "end_seconds": 15.0,
            "accepted_terms": True
        }
        
        with patch('app.api.jobs.q.enqueue') as mock_enqueue:
            mock_enqueue.return_value = MagicMock()
            response = client_with_mock_storage.post("/api/v1/jobs", json=job_data)
            job_id = response.json()["job_id"]
        
        # Simulate worker processing: manually add file to mock storage
        dummy_video_data = b"fake video content for testing"
        object_key = f"clips/{job_id}.mp4"
        
        # Store the dummy content directly in mock storage
        mock_storage._store[object_key] = dummy_video_data
        
        # Verify file was stored correctly
        assert object_key in mock_storage._store, f"File {object_key} not found in mock storage"
        stored_content = mock_storage.get_file_content(object_key)
        assert stored_content == dummy_video_data, "Stored content doesn't match dummy data"
        assert len(stored_content) == len(dummy_video_data), "Content length mismatch"
    
    def test_job_retrieval_with_presigned_url(self, client_with_mock_storage, mock_storage, fake_redis):
        """Test retrieving job returns 'done' status with memory:// presigned URL."""
        # Create job and simulate completion
        job_id = uuid.uuid4().hex
        object_key = f"clips/{job_id}.mp4"
        dummy_video_data = b"test video clip content"
        
        # Store file in mock storage
        mock_storage._store[object_key] = dummy_video_data
        
        # Set job status to 'done' in Redis
        job_data = {
            "id": job_id,
            "url": "https://www.youtube.com/watch?v=BaW_jenozKc",
            "in_ts": "5.0",
            "out_ts": "15.0",
            "status": "done",
            "progress": "None",
            "error_code": "None",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "object_key": object_key
        }
        fake_redis.hset(f"job:{job_id}", mapping=job_data)
        
        # Retrieve job status
        response = client_with_mock_storage.get(f"/api/v1/jobs/{job_id}")
        
        # Assert response contains correct status and mock URL
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["job_id"] == job_id, f"Job ID mismatch: expected {job_id}, got {data['job_id']}"
        assert data["status"] == "done", f"Expected status 'done', got '{data['status']}'"
        assert "link" in data, "Response missing download link"
        
        expected_url = f"memory://{object_key}"
        assert data["link"] == expected_url, f"Expected URL '{expected_url}', got '{data['link']}'"
    
    def test_download_via_mock_url(self, client_with_mock_storage, mock_storage):
        """Test downloading file content via mock storage methods."""
        # Prepare test data
        job_id = uuid.uuid4().hex
        object_key = f"clips/{job_id}.mp4"
        dummy_video_data = b"downloadable test video content"
        
        # Store file in mock storage
        mock_storage._store[object_key] = dummy_video_data
        
        # Generate presigned URL
        presigned_url = mock_storage.generate_presigned_url(object_key)
        expected_url = f"memory://{object_key}"
        assert presigned_url == expected_url, f"Expected URL '{expected_url}', got '{presigned_url}'"
        
        # Download content via mock storage
        downloaded_content = mock_storage.get_file_content(object_key)
        
        # Assert downloaded content matches original
        assert downloaded_content == dummy_video_data, "Downloaded content doesn't match original"
        assert len(downloaded_content) == len(dummy_video_data), "Downloaded content length mismatch"
        assert isinstance(downloaded_content, bytes), "Downloaded content should be bytes"
    
    def test_post_download_cleanup(self, client_with_mock_storage, mock_storage):
        """Test that cleanup logic deletes the file from mock storage after download."""
        # Prepare test data
        job_id = uuid.uuid4().hex
        object_key = f"clips/{job_id}.mp4"
        dummy_video_data = b"cleanup test video content"
        
        # Store file in mock storage
        mock_storage._store[object_key] = dummy_video_data
        
        # Verify file exists before cleanup
        assert object_key in mock_storage._store, f"File {object_key} should exist before cleanup"
        stored_keys_before = mock_storage.list_keys()
        assert object_key in stored_keys_before, "File should be in keys list before cleanup"
        
        # Simulate download completion and cleanup
        mock_storage.delete(object_key)
        
        # Verify file was deleted
        assert object_key not in mock_storage._store, f"File {object_key} should be deleted after cleanup"
        stored_keys_after = mock_storage.list_keys()
        assert object_key not in stored_keys_after, "File should not be in keys list after cleanup"
        
        # Verify attempting to access deleted file raises error
        with pytest.raises(FileNotFoundError) as exc_info:
            mock_storage.get_file_content(object_key)
        assert object_key in str(exc_info.value), "Error message should mention the missing key"
    
    def test_complete_job_flow_integration(self, client_with_mock_storage, mock_storage, fake_redis):
        """Test the complete job flow from creation to cleanup in one integrated test."""
        # 1. Create job
        job_data = {
            "url": "https://www.youtube.com/watch?v=BaW_jenozKc",
            "start_seconds": 10.0,
            "end_seconds": 25.0,
            "accepted_terms": True
        }
        
        with patch('app.api.jobs.q.enqueue') as mock_enqueue:
            mock_enqueue.return_value = MagicMock()
            response = client_with_mock_storage.post("/api/v1/jobs", json=job_data)
            
            assert response.status_code == 202, "Job creation failed"
            job_id = response.json()["job_id"]
            assert response.json()["status"] == "queued", "Job should start in queued status"
        
        # 2. Simulate worker upload
        dummy_video_data = b"complete integration test video content"
        object_key = f"clips/{job_id}.mp4"
        mock_storage._store[object_key] = dummy_video_data
        
        # Set job status to 'done' in Redis (simulating worker completion)
        job_completion_data = {
            "id": job_id,
            "url": "https://www.youtube.com/watch?v=BaW_jenozKc",
            "in_ts": "10.0",
            "out_ts": "25.0",
            "status": "done",
            "progress": "None",
            "error_code": "None",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "object_key": object_key
        }
        fake_redis.hset(f"job:{job_id}", mapping=job_completion_data)
        
        # 3. Retrieve job status
        response = client_with_mock_storage.get(f"/api/v1/jobs/{job_id}")
        
        assert response.status_code == 200, "Job retrieval failed"
        data = response.json()
        assert data["status"] == "done", "Job should be marked as done"
        assert data["link"] == f"memory://{object_key}", "Should return memory:// URL"
        
        # 4. Download via mock storage
        downloaded_content = mock_storage.get_file_content(object_key)
        assert downloaded_content == dummy_video_data, "Downloaded content should match original"
        
        # 5. Cleanup after download
        mock_storage.delete(object_key)
        assert object_key not in mock_storage._store, "File should be deleted after cleanup"
        
        # Verify complete cleanup
        remaining_keys = mock_storage.list_keys()
        assert object_key not in remaining_keys, "No traces of the file should remain"
    
    def test_mock_storage_isolation_between_tests(self, mock_storage):
        """Test that mock storage is properly isolated between tests."""
        # This test verifies that the mock_storage fixture properly cleans up
        # between tests, ensuring no leftover data from previous tests
        
        initial_keys = mock_storage.list_keys()
        assert len(initial_keys) == 0, f"Mock storage should be empty at test start, found: {initial_keys}"
        
        # Add some test data
        test_key = "isolation-test-file.mp4"
        test_data = b"isolation test content"
        mock_storage._store[test_key] = test_data
        
        # Verify data exists
        assert test_key in mock_storage.list_keys(), "Test data should be present"
        
        # The fixture should clean this up automatically after the test
        # This is verified by the next test starting with empty storage 