"""
Job service layer for handling video processing job business logic.
Separates business logic from HTTP concerns.
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from ..config.configuration import get_settings
from ..constants import ErrorMessages, JobStates, VideoConstraints
from ..exceptions import QueueFullError, ValidationError
from ..models import Job, JobCreateRequest, JobStatus
from ..queue.manager import QueueManager
from ..repositories.job_repository import JobRepository


class JobService:
    """Service layer for job management"""

    def __init__(self, repository: JobRepository, queue: QueueManager):
        self.repository = repository
        self.queue = queue
        self.settings = get_settings()

    async def create_job(self, request: JobCreateRequest) -> Job:
        """
        Create a new video processing job with validation

        Args:
            request: Job creation request with URL and parameters

        Returns:
            Created job instance

        Raises:
            QueueFullError: If queue is at capacity
            ValidationError: If request validation fails
        """
        # Validate queue capacity
        current_queue_size = await self.queue.get_queue_size()
        if current_queue_size >= self.settings.max_concurrent_jobs:
            raise QueueFullError(ErrorMessages.QUEUE_FULL)

        # Validate clip duration
        if request.end_time and request.start_time:
            duration = request.end_time - request.start_time
            if duration > VideoConstraints.MAX_CLIP_DURATION:
                raise ValidationError(ErrorMessages.CLIP_TOO_LONG)
            if duration < VideoConstraints.MIN_CLIP_DURATION:
                raise ValidationError(ErrorMessages.CLIP_TOO_SHORT)

        # Create job instance
        job = Job(
            id=str(uuid.uuid4()),
            url=request.url,
            start_time=request.start_time,
            end_time=request.end_time,
            format_id=request.format_id,
            state=JobStates.PENDING,
            created_at=datetime.utcnow(),
            progress=0,
            stage="Created",
        )

        # Persist job
        await self.repository.save(job)

        # Add to processing queue
        await self.queue.enqueue_job(job)

        return job

    async def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get job by ID

        Args:
            job_id: Unique job identifier

        Returns:
            Job instance if found, None otherwise
        """
        return await self.repository.get(job_id)

    async def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """
        Get job status with progress information

        Args:
            job_id: Unique job identifier

        Returns:
            Job status if found, None otherwise
        """
        job = await self.repository.get(job_id)
        if not job:
            return None

        return JobStatus(
            id=job.id,
            state=job.state,
            progress=job.progress,
            stage=job.stage,
            error=job.error,
            result=job.result,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )

    async def update_job_progress(
        self, job_id: str, progress: int, stage: str = None
    ) -> bool:
        """
        Update job progress and stage

        Args:
            job_id: Unique job identifier
            progress: Progress percentage (0-100)
            stage: Current processing stage

        Returns:
            True if updated successfully, False if job not found
        """
        job = await self.repository.get(job_id)
        if not job:
            return False

        job.progress = progress
        if stage:
            job.stage = stage
        job.updated_at = datetime.utcnow()

        await self.repository.save(job)
        return True

    async def complete_job(self, job_id: str, result: dict) -> bool:
        """
        Mark job as completed with result

        Args:
            job_id: Unique job identifier
            result: Processing result data

        Returns:
            True if updated successfully, False if job not found
        """
        job = await self.repository.get(job_id)
        if not job:
            return False

        job.state = JobStates.COMPLETED
        job.progress = 100
        job.stage = "Completed"
        job.result = result
        job.updated_at = datetime.utcnow()

        await self.repository.save(job)
        return True

    async def fail_job(self, job_id: str, error: str) -> bool:
        """
        Mark job as failed with error message

        Args:
            job_id: Unique job identifier
            error: Error message

        Returns:
            True if updated successfully, False if job not found
        """
        job = await self.repository.get(job_id)
        if not job:
            return False

        job.state = JobStates.FAILED
        job.stage = "Failed"
        job.error = error
        job.updated_at = datetime.utcnow()

        await self.repository.save(job)
        return True

    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a pending or running job

        Args:
            job_id: Unique job identifier

        Returns:
            True if cancelled successfully, False if job not found or cannot be cancelled
        """
        job = await self.repository.get(job_id)
        if not job:
            return False

        # Can only cancel pending or running jobs
        if job.state in [JobStates.COMPLETED, JobStates.FAILED, JobStates.CANCELLED]:
            return False

        # Remove from queue if still pending
        if job.state == JobStates.PENDING:
            await self.queue.remove_job(job_id)

        job.state = JobStates.CANCELLED
        job.stage = "Cancelled"
        job.updated_at = datetime.utcnow()

        await self.repository.save(job)
        return True

    async def get_queue_status(self) -> dict:
        """
        Get current queue status and statistics

        Returns:
            Dictionary with queue statistics
        """
        queue_size = await self.queue.get_queue_size()

        # Get job counts by state
        job_counts = await self.repository.get_job_counts_by_state()

        return {
            "queue_size": queue_size,
            "max_concurrent_jobs": self.settings.max_concurrent_jobs,
            "queue_capacity_used": queue_size / self.settings.max_concurrent_jobs,
            "job_counts": job_counts,
            "is_queue_full": queue_size >= self.settings.max_concurrent_jobs,
        }

    async def cleanup_expired_jobs(self) -> int:
        """
        Clean up expired jobs and their associated data

        Returns:
            Number of jobs cleaned up
        """
        cutoff_time = datetime.utcnow() - timedelta(
            hours=self.settings.cleanup_after_hours
        )
        return await self.repository.cleanup_jobs_before(cutoff_time)

    async def get_recent_jobs(self, limit: int = 10) -> List[Job]:
        """
        Get most recent jobs

        Args:
            limit: Maximum number of jobs to return

        Returns:
            List of recent jobs
        """
        return await self.repository.get_recent_jobs(limit)

    async def retry_failed_job(self, job_id: str) -> bool:
        """
        Retry a failed job

        Args:
            job_id: Unique job identifier

        Returns:
            True if retry was initiated, False otherwise
        """
        job = await self.repository.get(job_id)
        if not job or job.state != JobStates.FAILED:
            return False

        # Reset job state
        job.state = JobStates.PENDING
        job.progress = 0
        job.stage = "Retrying"
        job.error = None
        job.updated_at = datetime.utcnow()

        # Save and re-queue
        await self.repository.save(job)
        await self.queue.enqueue_job(job)

        return True
