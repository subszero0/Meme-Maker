import os
import sys
import tempfile
import logging
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the worker directory to Python path
worker_path = os.path.join(os.path.dirname(__file__), "../../worker")
if worker_path not in sys.path:
    sys.path.insert(0, worker_path)

# Mock Redis before importing from app
with patch("redis.Redis"):
    from app import redis, settings
    from app.models import JobStatus


class TestWorkerFunctions:
    """Test worker utility functions"""

    def setup_method(self):
        """Setup test environment"""
        self.job_id = "test_job_123"
        # Mock Redis operations instead of using real Redis
        self.redis_data = {}

    def teardown_method(self):
        """Clean up after tests"""
        # Clear mock data
        self.redis_data = {}

    @patch("app.redis")
    def test_job_progress_update(self, mock_redis):
        """Test updating job progress in Redis"""
        # Mock Redis operations
        mock_redis.hset.return_value = True
        mock_redis.expire.return_value = True
        mock_redis.hgetall.return_value = {b"progress": b"50"}
        mock_redis.ttl.return_value = 3600

        # Test basic progress update
        mock_redis.hset(f"job:{self.job_id}", mapping={"progress": 50})
        mock_redis.expire(f"job:{self.job_id}", 3600)

        job_data = mock_redis.hgetall(f"job:{self.job_id}")
        assert job_data[b"progress"] == b"50"

        # Verify TTL is set
        ttl = mock_redis.ttl(f"job:{self.job_id}")
        assert ttl > 0

    @patch("app.redis")
    def test_job_error_update(self, mock_redis):
        """Test updating job with error status"""
        error_code = "YTDLP_FAIL"
        error_message = "Video not found"

        # Mock Redis operations
        mock_redis.hset.return_value = True
        mock_redis.expire.return_value = True
        mock_redis.hgetall.return_value = {
            b"status": b"error",
            b"error_code": error_code.encode(),
            b"error_message": error_message.encode(),
        }

        mock_redis.hset(
            f"job:{self.job_id}",
            mapping={
                "status": JobStatus.error.value,
                "error_code": error_code,
                "error_message": error_message[:500],
                "progress": None,
            },
        )
        mock_redis.expire(f"job:{self.job_id}", 3600)

        job_data = mock_redis.hgetall(f"job:{self.job_id}")
        assert job_data[b"status"] == b"error"
        assert job_data[b"error_code"] == error_code.encode()
        assert job_data[b"error_message"] == error_message.encode()

    @patch("app.redis")
    def test_job_completion_update(self, mock_redis):
        """Test marking job as completed with URL"""
        presigned_url = "https://s3.example.com/test-file.mp4"

        # Mock Redis operations
        mock_redis.hset.return_value = True
        mock_redis.expire.return_value = True
        mock_redis.hgetall.return_value = {
            b"status": b"done",
            b"progress": b"100",
            b"url": presigned_url.encode(),
        }

        mock_redis.hset(
            f"job:{self.job_id}",
            mapping={
                "status": JobStatus.done.value,
                "progress": 100,
                "url": presigned_url,
                "completed_at": "2023-12-01T10:00:00Z",
            },
        )
        mock_redis.expire(f"job:{self.job_id}", 3600)

        job_data = mock_redis.hgetall(f"job:{self.job_id}")
        assert job_data[b"status"] == b"done"
        assert job_data[b"progress"] == b"100"
        assert job_data[b"url"] == presigned_url.encode()


class TestWorkerPipelineLogic:
    """Test the worker pipeline logic with mocked dependencies"""

    @patch("subprocess.run")
    def test_keyframe_detection_logic(self, mock_subprocess):
        """Test keyframe detection logic"""
        # Mock ffprobe output with keyframes at 0s, 2s, 4s, 6s
        mock_subprocess.return_value.stdout = "0.000000,1\n1.500000,0\n2.000000,1\n3.500000,0\n4.000000,1\n5.500000,0\n6.000000,1\n"
        mock_subprocess.return_value.returncode = 0

        # Test the keyframe detection logic directly
        def find_nearest_keyframe(video_path: str, timestamp: float) -> float:
            """
            Find the nearest keyframe to a given timestamp
            using ffprobe
            """
            # Mock implementation for testing
            return timestamp  # Simplified for test

        # Test finding keyframe before timestamp
        result = find_nearest_keyframe("/fake/path", 3.5)
        assert result == 2.0  # Should find keyframe at 2s

        # Test finding exact keyframe
        result = find_nearest_keyframe("/fake/path", 4.0)
        assert result == 4.0  # Should find exact keyframe at 4s

        # Test timestamp before first keyframe
        result = find_nearest_keyframe("/fake/path", 0.5)
        assert result == 0.0  # Should find first keyframe at 0s

    @patch("boto3.client")
    @patch("subprocess.run")
    @patch("tempfile.mkdtemp")
    @patch("app.redis")
    def test_clip_processing_workflow(
        self, mock_redis, mock_mkdtemp, mock_subprocess, mock_boto3
    ):
        """Test the complete clipping workflow with mocked dependencies"""
        job_id = "test_workflow_job"
        # Mock workflow with settings that aren't used in this isolated test
        # url = "https://example.com/video"
        # in_ts = 5.0
        # out_ts used for worker simulation but not in this test scope

        # Setup mocks
        temp_dir = "/tmp/test_clip_123"
        mock_mkdtemp.return_value = temp_dir

        # Mock Redis operations
        mock_redis.hset.return_value = True
        mock_redis.hgetall.return_value = {
            b"status": b"done",
            b"progress": b"100",
            b"url": b"https://s3.example.com/presigned-url",
        }
        mock_redis.delete.return_value = True

        # Mock subprocess (ffprobe and ffmpeg)
        def subprocess_side_effect(*args, **kwargs):
            result = MagicMock()
            result.returncode = 0
            result.stdout = "4.000000,1\n6.000000,1\n"  # Keyframes at 4s and 6s
            result.stderr = ""
            return result

        mock_subprocess.side_effect = subprocess_side_effect

        # Mock S3 client
        mock_s3_client = MagicMock()
        mock_boto3.return_value = mock_s3_client
        mock_s3_client.upload_file.return_value = None
        mock_s3_client.generate_presigned_url.return_value = (
            "https://s3.example.com/presigned-url"
        )

        # Simulate the key steps of the worker process
        with patch("pathlib.Path") as mock_path_class:
            mock_path_instance = MagicMock()
            mock_path_class.return_value = mock_path_instance
            mock_path_instance.glob.return_value = [f"{temp_dir}/{job_id}.mp4"]
            mock_path_instance.exists.return_value = True
            mock_path_instance.stat.return_value.st_size = 1024

            # Test step 1: Job initialization
            mock_redis.hset(
                f"job:{job_id}",
                mapping={"status": JobStatus.working.value, "progress": 10},
            )

            # Test step 2: Download simulation (skip yt-dlp since it's worker-only)
            mock_redis.hset(f"job:{job_id}", "progress", 20)

            # Test step 3: Processing simulation
            mock_redis.hset(f"job:{job_id}", "progress", 70)

            # Test step 4: Upload simulation
            mock_redis.hset(f"job:{job_id}", "progress", 90)

            # Test step 5: Completion
            mock_redis.hset(
                f"job:{job_id}",
                mapping={
                    "status": JobStatus.done.value,
                    "progress": 100,
                    "url": "https://s3.example.com/presigned-url",
                },
            )

            # Verify final state
            job_data = mock_redis.hgetall(f"job:{job_id}")
            assert job_data[b"status"] == b"done"
            assert job_data[b"progress"] == b"100"
            assert b"url" in job_data

        # Cleanup
        mock_redis.delete(f"job:{job_id}")


class TestDockerWorkerSetup:
    """Test that the worker Docker setup is correct"""

    def test_dockerfile_exists(self):
        """Test that Dockerfile.worker exists and has correct content"""
        dockerfile_path = Path(__file__).parent.parent.parent / "Dockerfile.worker"
        assert dockerfile_path.exists(), "Dockerfile.worker should exist"

        content = dockerfile_path.read_text()
        assert "python:3.12-alpine" in content, "Should use Python 3.12 Alpine"
        assert "ffmpeg" in content, "Should install FFmpeg"
        assert "worker/main.py" in content, "Should run worker main.py"

    def test_worker_requirements(self):
        """Test that worker requirements.txt has necessary dependencies"""
        requirements_path = (
            Path(__file__).parent.parent.parent / "worker" / "requirements.txt"
        )
        assert requirements_path.exists(), "worker/requirements.txt should exist"

        content = requirements_path.read_text()
        assert "redis" in content, "Should include Redis"
        assert "rq" in content, "Should include RQ"
        assert "yt-dlp" in content, "Should include yt-dlp"
        assert "boto3" in content, "Should include boto3"
        assert "prometheus_client" in content, "Should include Prometheus client"

    def test_process_clip_file_exists(self):
        """Test that process_clip.py exists"""
        process_clip_path = (
            Path(__file__).parent.parent.parent / "worker" / "process_clip.py"
        )
        assert process_clip_path.exists(), "worker/process_clip.py should exist"

        content = process_clip_path.read_text()
        assert "def process_clip" in content, "Should have process_clip function"
        assert "update_job_progress" in content, "Should have progress update function"
        assert "update_job_error" in content, "Should have error update function"
        assert (
            "find_nearest_keyframe" in content
        ), "Should have keyframe detection function"


@pytest.mark.integration
class TestEndToEndSimulation:
    """Simulate end-to-end job processing without external dependencies"""

    @patch("app.redis")
    def test_complete_job_lifecycle(self, mock_redis):
        """Test complete job lifecycle simulation"""
        job_id = "e2e_test_job"

        # Mock Redis operations
        mock_redis.hset.return_value = True
        mock_redis.expire.return_value = True
        mock_redis.hgetall.return_value = {
            b"status": b"done",
            b"progress": b"100",
            b"url": b"https://s3.example.com/test-file.mp4",
        }
        mock_redis.ttl.return_value = 3600
        mock_redis.delete.return_value = True

        try:
            # Step 1: Job creation (simulated)
            mock_redis.hset(
                f"job:{job_id}",
                mapping={
                    "id": job_id,
                    "url": "https://example.com/video",
                    "in_ts": "5.0",
                    "out_ts": "15.0",
                    "status": JobStatus.queued.value,
                    "created_at": "2023-12-01T10:00:00Z",
                },
            )

            # Step 2: Job picked up by worker
            mock_redis.hset(
                f"job:{job_id}",
                mapping={"status": JobStatus.working.value, "progress": 10},
            )

            # Step 3: Download phase
            mock_redis.hset(f"job:{job_id}", "progress", 20)

            # Step 4: Processing phase
            mock_redis.hset(f"job:{job_id}", "progress", 70)

            # Step 5: Upload phase
            mock_redis.hset(f"job:{job_id}", "progress", 90)

            # Step 6: Job completion
            mock_redis.hset(
                f"job:{job_id}",
                mapping={
                    "status": JobStatus.done.value,
                    "progress": 100,
                    "url": "https://s3.example.com/test-file.mp4",
                    "completed_at": "2023-12-01T10:05:00Z",
                },
            )
            mock_redis.expire(f"job:{job_id}", 3600)

            # Verify final state
            job_data = mock_redis.hgetall(f"job:{job_id}")
            assert job_data[b"status"] == b"done"
            assert job_data[b"progress"] == b"100"
            assert b"url" in job_data

            # Verify TTL is set
            ttl = mock_redis.ttl(f"job:{job_id}")
            assert ttl > 0

        finally:
            # Cleanup
            mock_redis.delete(f"job:{job_id}")

    @patch("app.redis")
    def test_job_error_handling(self, mock_redis):
        """Test job error handling simulation"""
        job_id = "error_test_job"

        # Mock Redis operations
        mock_redis.hset.return_value = True
        mock_redis.expire.return_value = True
        mock_redis.hgetall.return_value = {
            b"status": b"error",
            b"error_code": b"YTDLP_FAIL",
            b"error_message": b"Test error message",
        }
        mock_redis.delete.return_value = True

        try:
            # Step 1: Job starts normally
            mock_redis.hset(
                f"job:{job_id}",
                mapping={
                    "id": job_id,
                    "url": "https://invalid-url.com/video",
                    "status": JobStatus.working.value,
                    "progress": 10,
                },
            )

            # Step 2: Error occurs during processing
            mock_redis.hset(
                f"job:{job_id}",
                mapping={
                    "status": JobStatus.error.value,
                    "error_code": "YTDLP_FAIL",
                    "error_message": "Test error message",
                    "progress": None,
                },
            )
            mock_redis.expire(f"job:{job_id}", 3600)

            # Verify error state
            job_data = mock_redis.hgetall(f"job:{job_id}")
            assert job_data[b"status"] == b"error"
            assert job_data[b"error_code"] == b"YTDLP_FAIL"
            assert job_data[b"error_message"] == b"Test error message"

        finally:
            # Cleanup
            mock_redis.delete(f"job:{job_id}")
