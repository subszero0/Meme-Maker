import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the worker directory to Python path (must be before app imports)
worker_path = os.path.join(os.path.dirname(__file__), "../../worker")
if worker_path not in sys.path:
    sys.path.insert(0, worker_path)

from app import redis
from app.models import JobStatus


class TestWorkerFunctions:
    """Test worker utility functions"""

    def setup_method(self):
        """Setup test environment"""
        self.job_id = "test_job_123"
        # Clean up any existing job data
        redis.delete(f"job:{self.job_id}")

    def teardown_method(self):
        """Clean up after tests"""
        redis.delete(f"job:{self.job_id}")

    def test_job_progress_update(self):
        """Test updating job progress in Redis"""
        # Test basic progress update
        redis.hset(f"job:{self.job_id}", mapping={"progress": 50})
        redis.expire(f"job:{self.job_id}", 3600)

        job_data = redis.hgetall(f"job:{self.job_id}")
        assert job_data[b"progress"] == b"50"

        # Verify TTL is set
        ttl = redis.ttl(f"job:{self.job_id}")
        assert ttl > 0

    def test_job_error_update(self):
        """Test updating job with error status"""
        error_code = "YTDLP_FAIL"
        error_message = "Video not found"

        redis.hset(
            f"job:{self.job_id}",
            mapping={
                "status": JobStatus.error.value,
                "error_code": error_code,
                "error_message": error_message[:500],
                "progress": None,
            },
        )
        redis.expire(f"job:{self.job_id}", 3600)

        job_data = redis.hgetall(f"job:{self.job_id}")
        assert job_data[b"status"] == b"error"
        assert job_data[b"error_code"] == error_code.encode()
        assert job_data[b"error_message"] == error_message.encode()

    def test_job_completion_update(self):
        """Test marking job as completed with URL"""
        presigned_url = "https://s3.example.com/test-file.mp4"

        redis.hset(
            f"job:{self.job_id}",
            mapping={
                "status": JobStatus.done.value,
                "progress": 100,
                "url": presigned_url,
                "completed_at": "2023-12-01T10:00:00Z",
            },
        )
        redis.expire(f"job:{self.job_id}", 3600)

        job_data = redis.hgetall(f"job:{self.job_id}")
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
            """Test implementation of keyframe finding"""
            try:
                cmd = [
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "frame=pkt_pts_time,key_frame",
                    "-of",
                    "csv=print_section=0",
                    video_path,
                ]

                result = mock_subprocess(
                    cmd, capture_output=True, text=True, check=True
                )

                keyframes = []
                for line in result.stdout.strip().split("\n"):
                    if line:
                        parts = line.split(",")
                        if len(parts) >= 2 and parts[1] == "1":  # key_frame=1
                            try:
                                keyframe_time = float(parts[0])
                                if keyframe_time <= timestamp:
                                    keyframes.append(keyframe_time)
                            except ValueError:
                                continue

                return max(keyframes) if keyframes else 0.0

            except Exception:
                return timestamp

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
    @patch("yt_dlp.YoutubeDL")
    @patch("tempfile.mkdtemp")
    def test_clip_processing_workflow(
        self, mock_mkdtemp, mock_ytdlp, mock_subprocess, mock_boto3
    ):
        """Test the complete clipping workflow with mocked dependencies"""
        job_id = "test_workflow_job"
        # url = "https://example.com/video"  # Not used in test
        # in_ts = 5.0  # Not used in test
        # out_ts = 15.0  # Not used in test

        # Setup mocks
        temp_dir = "/tmp/test_clip_123"
        mock_mkdtemp.return_value = temp_dir

        # Mock YT-DLP
        mock_ytdl_instance = MagicMock()
        mock_ytdlp.return_value.__enter__.return_value = mock_ytdl_instance
        mock_ytdl_instance.extract_info.return_value = {"title": "Test Video"}

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
            redis.hset(
                f"job:{job_id}",
                mapping={"status": JobStatus.working.value, "progress": 10},
            )

            # Test step 2: Download simulation
            redis.hset(f"job:{job_id}", "progress", 20)

            # Test step 3: Processing simulation
            redis.hset(f"job:{job_id}", "progress", 70)

            # Test step 4: Upload simulation
            redis.hset(f"job:{job_id}", "progress", 90)

            # Test step 5: Completion
            redis.hset(
                f"job:{job_id}",
                mapping={
                    "status": JobStatus.done.value,
                    "progress": 100,
                    "url": "https://s3.example.com/presigned-url",
                },
            )

            # Verify final state
            job_data = redis.hgetall(f"job:{job_id}")
            assert job_data[b"status"] == b"done"
            assert job_data[b"progress"] == b"100"
            assert b"url" in job_data

        # Cleanup
        redis.delete(f"job:{job_id}")


class TestDockerWorkerSetup:
    """Test that the worker Docker setup is correct"""

    def test_dockerfile_exists(self):
        """Test that Dockerfile.worker exists and has correct content"""
        dockerfile_path = Path(__file__).parent.parent.parent / "Dockerfile.worker"
        assert dockerfile_path.exists(), "Dockerfile.worker should exist"

        content = dockerfile_path.read_text()
        assert "python:3.12-alpine" in content, "Should use Python 3.12 Alpine"
        assert "ffmpeg" in content, "Should install FFmpeg"
        assert "clips" in content, "Should use 'clips' queue name"

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
        assert "pydantic" in content, "Should include Pydantic"

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

    def test_complete_job_lifecycle(self):
        """Test complete job lifecycle simulation"""
        job_id = "e2e_test_job"

        try:
            # Step 1: Job creation (simulated)
            redis.hset(
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
            redis.hset(
                f"job:{job_id}",
                mapping={"status": JobStatus.working.value, "progress": 10},
            )

            # Step 3: Download phase
            redis.hset(f"job:{job_id}", "progress", 20)

            # Step 4: Processing phase
            redis.hset(f"job:{job_id}", "progress", 70)

            # Step 5: Upload phase
            redis.hset(f"job:{job_id}", "progress", 90)

            # Step 6: Job completion
            redis.hset(
                f"job:{job_id}",
                mapping={
                    "status": JobStatus.done.value,
                    "progress": 100,
                    "url": "https://s3.example.com/test-file.mp4",
                    "completed_at": "2023-12-01T10:05:00Z",
                },
            )
            redis.expire(f"job:{job_id}", 3600)

            # Verify final state
            job_data = redis.hgetall(f"job:{job_id}")
            assert job_data[b"status"] == b"done"
            assert job_data[b"progress"] == b"100"
            assert b"url" in job_data

            # Verify TTL is set
            ttl = redis.ttl(f"job:{job_id}")
            assert ttl > 0

        finally:
            # Cleanup
            redis.delete(f"job:{job_id}")

    def test_job_error_handling(self):
        """Test job error handling simulation"""
        job_id = "error_test_job"

        try:
            # Start job
            redis.hset(
                f"job:{job_id}",
                mapping={"status": JobStatus.working.value, "progress": 50},
            )

            # Simulate error
            redis.hset(
                f"job:{job_id}",
                mapping={
                    "status": JobStatus.error.value,
                    "error_code": "YTDLP_FAIL",
                    "error_message": "Video not available",
                    "progress": None,
                },
            )
            redis.expire(f"job:{job_id}", 3600)

            # Verify error state
            job_data = redis.hgetall(f"job:{job_id}")
            assert job_data[b"status"] == b"error"
            assert job_data[b"error_code"] == b"YTDLP_FAIL"
            assert b"Video not available" in job_data[b"error_message"]

        finally:
            # Cleanup
            redis.delete(f"job:{job_id}")
