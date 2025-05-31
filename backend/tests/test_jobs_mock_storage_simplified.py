"""
Simplified tests for job flow with mock storage.

This module tests the job flow components using the InMemoryStorage mock
without importing the full FastAPI app to avoid aioredis import issues.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock

from app.utils.mock_storage import InMemoryStorage


class TestJobFlowMockStorageSimplified:
    """Test job flow components with mock storage."""
    
    def test_mock_storage_initialization(self):
        """Test that InMemoryStorage initializes correctly."""
        storage = InMemoryStorage()
        
        assert storage._store == {}, "Storage should start with empty store"
        assert storage.list_keys() == [], "Should return empty list initially"
        
    def test_job_data_simulation_with_mock_storage(self):
        """Test simulating job data storage and retrieval."""
        storage = InMemoryStorage()
        
        # Simulate job creation
        job_id = uuid.uuid4().hex
        object_key = f"clips/{job_id}.mp4"
        
        # Simulate worker upload
        dummy_video_data = b"test video content for job flow"
        storage._store[object_key] = dummy_video_data
        
        # Verify upload worked
        assert object_key in storage._store, f"Object {object_key} should be in storage"
        assert object_key in storage.list_keys(), f"Object {object_key} should be in keys list"
        
        # Test content retrieval
        retrieved_content = storage.get_file_content(object_key)
        assert retrieved_content == dummy_video_data, "Retrieved content should match original"
        assert len(retrieved_content) == len(dummy_video_data), "Content length should match"
    
    def test_presigned_url_generation_for_job(self):
        """Test generating presigned URLs for job downloads."""
        storage = InMemoryStorage()
        
        # Setup job data
        job_id = uuid.uuid4().hex
        object_key = f"clips/{job_id}.mp4"
        dummy_data = b"presigned URL test content"
        storage._store[object_key] = dummy_data
        
        # Generate presigned URL
        presigned_url = storage.generate_presigned_url(object_key)
        
        # Verify URL format
        expected_url = f"memory://{object_key}"
        assert presigned_url == expected_url, f"Expected {expected_url}, got {presigned_url}"
        
        # Verify URL points to existing content
        content = storage.get_file_content(object_key)
        assert content == dummy_data, "URL should point to correct content"
    
    def test_job_cleanup_simulation(self):
        """Test simulating job cleanup after download."""
        storage = InMemoryStorage()
        
        # Setup multiple job files
        job_ids = [uuid.uuid4().hex for _ in range(3)]
        object_keys = [f"clips/{job_id}.mp4" for job_id in job_ids]
        
        # Store files
        for i, key in enumerate(object_keys):
            storage._store[key] = f"content for job {i}".encode()
        
        # Verify all files exist
        assert len(storage.list_keys()) == 3, "Should have 3 files"
        for key in object_keys:
            assert key in storage._store, f"File {key} should exist"
        
        # Simulate cleanup of first job
        storage.delete(object_keys[0])
        
        # Verify cleanup
        assert object_keys[0] not in storage._store, "First file should be deleted"
        assert object_keys[0] not in storage.list_keys(), "First file should not be in keys"
        assert len(storage.list_keys()) == 2, "Should have 2 files remaining"
        
        # Verify other files still exist
        for key in object_keys[1:]:
            assert key in storage._store, f"File {key} should still exist"
    
    def test_error_handling_for_missing_files(self):
        """Test error handling when accessing non-existent files."""
        storage = InMemoryStorage()
        
        nonexistent_key = "clips/nonexistent-job.mp4"
        
        # Test get_file_content error
        with pytest.raises(FileNotFoundError) as exc_info:
            storage.get_file_content(nonexistent_key)
        assert nonexistent_key in str(exc_info.value), "Error should mention the missing key"
        
        # Test presigned URL generation error
        with pytest.raises(FileNotFoundError) as exc_info:
            storage.generate_presigned_url(nonexistent_key)
        assert nonexistent_key in str(exc_info.value), "Error should mention the missing key"
        
        # Test delete non-existent file (should not raise error)
        storage.delete(nonexistent_key)  # Should complete without error
    
    def test_complete_job_lifecycle_simulation(self):
        """Test the complete job lifecycle from creation to cleanup."""
        storage = InMemoryStorage()
        
        # 1. Job Creation Phase
        job_id = uuid.uuid4().hex
        object_key = f"clips/{job_id}.mp4"
        
        # Initially no files
        assert len(storage.list_keys()) == 0, "Storage should start empty"
        
        # 2. Worker Processing Phase
        dummy_video_data = b"complete lifecycle test video content"
        storage._store[object_key] = dummy_video_data
        
        # Verify upload
        assert object_key in storage.list_keys(), "File should exist after upload"
        assert len(storage.list_keys()) == 1, "Should have exactly one file"
        
        # 3. Job Completion Phase
        # Generate download URL
        download_url = storage.generate_presigned_url(object_key)
        assert download_url.startswith("memory://"), "Should be a memory URL"
        assert object_key in download_url, "URL should contain the object key"
        
        # 4. Download Simulation Phase
        downloaded_content = storage.get_file_content(object_key)
        assert downloaded_content == dummy_video_data, "Downloaded content should match"
        
        # 5. Cleanup Phase
        storage.delete(object_key)
        assert object_key not in storage._store, "File should be deleted"
        assert len(storage.list_keys()) == 0, "Storage should be empty after cleanup"
        
        # Verify complete cleanup
        with pytest.raises(FileNotFoundError):
            storage.get_file_content(object_key)
    
    def test_storage_isolation_between_job_instances(self):
        """Test that different storage instances don't interfere with each other."""
        storage1 = InMemoryStorage()
        storage2 = InMemoryStorage()
        
        # Add different data to each storage
        job1_key = "clips/job1.mp4"
        job2_key = "clips/job2.mp4"
        
        storage1._store[job1_key] = b"job1 content"
        storage2._store[job2_key] = b"job2 content"
        
        # Verify isolation
        assert job1_key in storage1.list_keys(), "Job1 should be in storage1"
        assert job1_key not in storage2.list_keys(), "Job1 should not be in storage2"
        assert job2_key in storage2.list_keys(), "Job2 should be in storage2"
        assert job2_key not in storage1.list_keys(), "Job2 should not be in storage1"
        
        # Verify content isolation
        assert storage1.get_file_content(job1_key) == b"job1 content"
        assert storage2.get_file_content(job2_key) == b"job2 content"
        
        # Verify cross-access fails
        with pytest.raises(FileNotFoundError):
            storage1.get_file_content(job2_key)
        with pytest.raises(FileNotFoundError):
            storage2.get_file_content(job1_key)
    
    def test_concurrent_job_simulation(self):
        """Test simulating multiple concurrent jobs in the same storage."""
        storage = InMemoryStorage()
        
        # Create multiple jobs
        num_jobs = 5
        job_data = {}
        
        for i in range(num_jobs):
            job_id = uuid.uuid4().hex
            object_key = f"clips/{job_id}.mp4"
            content = f"job {i} video content".encode()
            
            storage._store[object_key] = content
            job_data[job_id] = (object_key, content)
        
        # Verify all jobs exist
        assert len(storage.list_keys()) == num_jobs, f"Should have {num_jobs} files"
        
        # Verify each job's content
        for job_id, (object_key, expected_content) in job_data.items():
            actual_content = storage.get_file_content(object_key)
            assert actual_content == expected_content, f"Content mismatch for job {job_id}"
            
            # Verify presigned URL generation
            url = storage.generate_presigned_url(object_key)
            assert url == f"memory://{object_key}", f"URL mismatch for job {job_id}"
        
        # Simulate some jobs completing (cleanup)
        completed_jobs = list(job_data.keys())[:3]  # First 3 jobs complete
        
        for job_id in completed_jobs:
            object_key = job_data[job_id][0]
            storage.delete(object_key)
        
        # Verify partial cleanup
        remaining_keys = storage.list_keys()
        assert len(remaining_keys) == num_jobs - 3, "Should have 2 files remaining"
        
        # Verify remaining jobs still work
        for job_id, (object_key, expected_content) in job_data.items():
            if job_id not in completed_jobs:
                actual_content = storage.get_file_content(object_key)
                assert actual_content == expected_content, f"Remaining job {job_id} should still work" 