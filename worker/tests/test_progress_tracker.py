"""
Unit tests for ProgressTracker
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add worker directory to path for imports
worker_dir = Path(__file__).parent.parent
sys.path.insert(0, str(worker_dir))


class TestProgressTracker:
    """Test ProgressTracker functionality with mocked dependencies"""

    @patch("progress.tracker.JobStatus")
    @patch("progress.tracker.redis")
    def test_progress_tracker_creation(self, mock_redis, mock_job_status):
        """Test creating a ProgressTracker instance"""
        from progress.tracker import ProgressTracker

        tracker = ProgressTracker("test_job_123")
        assert tracker.job_id == "test_job_123"
        assert tracker.redis == mock_redis

    @patch("progress.tracker.logger")
    @patch("progress.tracker.redis")
    def test_update_progress_success(self, mock_redis, mock_logger):
        """Test successful progress update"""
        from progress.tracker import ProgressTracker

        tracker = ProgressTracker("test_job_123")

        # Test basic progress update
        tracker.update(50)

        # Verify Redis calls
        mock_redis.hset.assert_called_once_with(
            "job:test_job_123", mapping={"progress": "50"}
        )
        mock_redis.expire.assert_called_once_with("job:test_job_123", 3600)

        # Verify logging
        mock_logger.info.assert_called_once()
        log_call_args = mock_logger.info.call_args[0][0]
        assert "test_job_123" in log_call_args
        assert "50%" in log_call_args

    @patch("progress.tracker.logger")
    @patch("progress.tracker.redis")
    def test_update_progress_with_status_and_stage(self, mock_redis, mock_logger):
        """Test progress update with status and stage"""
        from progress.tracker import ProgressTracker

        tracker = ProgressTracker("test_job_123")

        # Test progress update with status and stage
        tracker.update(75, status="working", stage="Processing video")

        # Verify Redis calls
        mock_redis.hset.assert_called_once_with(
            "job:test_job_123",
            mapping={
                "progress": "75",
                "status": "working",
                "stage": "Processing video",
            },
        )
        mock_redis.expire.assert_called_once_with("job:test_job_123", 3600)

    @patch("progress.tracker.logger")
    @patch("progress.tracker.redis")
    def test_update_progress_redis_failure(self, mock_redis, mock_logger):
        """Test handling Redis failure during progress update"""
        from progress.tracker import ProgressTracker

        # Make Redis fail
        mock_redis.hset.side_effect = Exception("Redis connection failed")

        tracker = ProgressTracker("test_job_123")

        # Update should not raise exception
        tracker.update(50)

        # Verify error was logged
        mock_logger.error.assert_called_once()
        error_log = mock_logger.error.call_args[0][0]
        assert "test_job_123" in error_log
        assert "Failed to update job progress" in error_log

    @patch("progress.tracker.logger")
    @patch("progress.tracker.JobStatus")
    @patch("progress.tracker.redis")
    def test_update_error_success(self, mock_redis, mock_job_status, mock_logger):
        """Test successful error update"""
        from progress.tracker import ProgressTracker

        # Mock JobStatus.error.value
        mock_job_status.error.value = "error"

        tracker = ProgressTracker("test_job_123")

        # Test error update
        tracker.update_error("DOWNLOAD_FAILED", "Could not download video")

        # Verify Redis calls
        expected_mapping = {
            "status": "error",
            "error_code": "DOWNLOAD_FAILED",
            "error_message": "Could not download video",
            "progress": "0",
        }
        mock_redis.hset.assert_called_once_with(
            "job:test_job_123", mapping=expected_mapping
        )
        mock_redis.expire.assert_called_once_with("job:test_job_123", 3600)

        # Verify logging
        mock_logger.info.assert_called_once()
        log_call_args = mock_logger.info.call_args[0][0]
        assert "test_job_123" in log_call_args
        assert "DOWNLOAD_FAILED" in log_call_args

    @patch("progress.tracker.logger")
    @patch("progress.tracker.JobStatus")
    @patch("progress.tracker.redis")
    def test_update_error_truncates_long_message(
        self, mock_redis, mock_job_status, mock_logger
    ):
        """Test that long error messages are truncated"""
        from progress.tracker import ProgressTracker

        mock_job_status.error.value = "error"

        tracker = ProgressTracker("test_job_123")

        # Create a long error message (over 500 chars)
        long_message = "A" * 600

        tracker.update_error("LONG_ERROR", long_message)

        # Verify message was truncated to 500 chars
        call_args = mock_redis.hset.call_args[1]["mapping"]
        assert len(call_args["error_message"]) == 500
        assert call_args["error_message"] == "A" * 500

    @patch("progress.tracker.logger")
    @patch("progress.tracker.JobStatus")
    @patch("progress.tracker.redis")
    def test_update_error_redis_failure(self, mock_redis, mock_job_status, mock_logger):
        """Test handling Redis failure during error update"""
        from progress.tracker import ProgressTracker

        mock_job_status.error.value = "error"

        # Make Redis fail
        mock_redis.hset.side_effect = Exception("Redis connection failed")

        tracker = ProgressTracker("test_job_123")

        # Update should not raise exception
        tracker.update_error("TEST_ERROR", "Test message")

        # Verify error was logged
        mock_logger.error.assert_called_once()
        error_log = mock_logger.error.call_args[0][0]
        assert "test_job_123" in error_log
        assert "Failed to update job error" in error_log

    @patch("progress.tracker.logger")
    @patch("progress.tracker.redis")
    def test_structured_logging_extra_data(self, mock_redis, mock_logger):
        """Test that structured logging includes extra data"""
        from progress.tracker import ProgressTracker

        tracker = ProgressTracker("test_job_123")

        tracker.update(80, status="working", stage="Uploading")

        # Verify logging was called with extra data
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args

        # Check that extra data was passed
        assert "extra" in call_args[1]
        extra_data = call_args[1]["extra"]
        assert extra_data["job_id"] == "test_job_123"
        assert extra_data["progress"] == 80
        assert extra_data["stage"] == "Uploading"
        assert extra_data["status"] == "working"


if __name__ == "__main__":
    pytest.main([__file__])
