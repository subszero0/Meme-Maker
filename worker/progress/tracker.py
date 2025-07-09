"""
Progress Tracker for Video Processing Jobs

Handles job progress updates with correlation ID logging and Redis operations.
"""

import logging
from typing import Optional

# Try to import from backend app, but handle gracefully for testing
try:
    import sys

    sys.path.append("/app/backend")
    from app import redis
    from app.models import JobStatus
except ImportError:
    # For testing or standalone usage, use mock imports
    redis = None

    class JobStatus:
        class error:
            value = "error"


logger = logging.getLogger(__name__)


class ProgressTracker:
    """Manages job progress tracking with Redis persistence and structured logging"""

    def __init__(self, job_id: str, redis_client=None):
        """
        Initialize progress tracker

        Args:
            job_id: Unique job identifier
            redis_client: Optional Redis client for dependency injection
        """
        self.job_id = job_id
        # Use provided redis_client, or fall back to global redis
        # This ensures compatibility with existing tests that mock the global redis
        self.redis = redis_client if redis_client is not None else redis

    def update(
        self, progress: int, status: Optional[str] = None, stage: Optional[str] = None
    ) -> None:
        """
        Update job progress with correlation ID logging

        Args:
            progress: Progress percentage (0-100)
            status: Optional job status
            stage: Optional processing stage description
        """
        try:
            # Check if Redis is available (but allow mocked Redis)
            if self.redis is None:
                logger.warning(f"No Redis client available for job {self.job_id}")
                return

            job_key = f"job:{self.job_id}"
            update_data = {"progress": str(progress)}  # Convert to string for Redis

            if status:
                update_data["status"] = str(status)
            if stage:
                update_data["stage"] = str(stage)

            self.redis.hset(job_key, mapping=update_data)
            self.redis.expire(job_key, 3600)  # 1 hour expiry

            # Structured logging with correlation ID
            stage_msg = f" - {stage}" if stage else ""
            logger.info(
                f"📊 Job {self.job_id} progress: {progress}% {f'({status})' if status else ''}{stage_msg}",
                extra={
                    "job_id": self.job_id,
                    "progress": progress,
                    "stage": stage,
                    "status": status,
                },
            )

        except Exception as e:
            logger.error(
                f"❌ Failed to update job progress for {self.job_id}: {e}",
                extra={"job_id": self.job_id, "error": str(e)},
            )

    def update_error(self, error_code: str, error_message: str) -> None:
        """
        Update job with error status and details

        Args:
            error_code: Error classification code
            error_message: Detailed error message
        """
        try:
            # Check if Redis is available (but allow mocked Redis)
            if self.redis is None:
                logger.warning(f"No Redis client available for job {self.job_id}")
                return

            job_key = f"job:{self.job_id}"
            # Convert all values to strings to avoid Redis type errors
            mapping_data = {
                "status": str(JobStatus.error.value),
                "error_code": str(error_code),
                "error_message": str(
                    error_message[:500]
                ),  # Truncate long error messages
                "progress": "0",  # Use "0" instead of null for error state
            }

            self.redis.hset(job_key, mapping=mapping_data)
            self.redis.expire(job_key, 3600)

            logger.info(
                f"✅ Updated job {self.job_id} with error status: {error_code}",
                extra={
                    "job_id": self.job_id,
                    "error_code": error_code,
                    "error_message": error_message[:100],  # Log truncated version
                },
            )

        except Exception as e:
            logger.error(
                f"❌ Failed to update job error for {self.job_id}: {e}",
                extra={"job_id": self.job_id, "error": str(e)},
            )
