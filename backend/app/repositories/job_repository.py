"""
Job repository layer for data access operations.
Simplified version for testing configuration.
"""
from datetime import datetime
from typing import Dict, List, Optional

from ..models import Job


class JobRepository:
    """Simplified repository for testing"""

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._jobs = {}  # In-memory storage for testing

    async def save(self, job: Job) -> None:
        """Save job"""
        self._jobs[job.id] = job

    async def get(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        return self._jobs.get(job_id)

    async def get_job_counts_by_state(self) -> Dict[str, int]:
        """Get count of jobs by state"""
        counts: Dict[str, int] = {}
        for job in self._jobs.values():
            state = job.state or "pending"
            counts[state] = counts.get(state, 0) + 1
        return counts

    async def cleanup_jobs_before(self, cutoff_time: datetime) -> int:
        """Clean up old jobs"""
        count = 0
        to_remove = []
        for job_id, job in self._jobs.items():
            if job.created_at < cutoff_time:
                to_remove.append(job_id)
                count += 1

        for job_id in to_remove:
            del self._jobs[job_id]

        return count

    async def get_recent_jobs(self, limit: int = 10) -> List[Job]:
        """Get recent jobs"""
        jobs = list(self._jobs.values())
        jobs.sort(key=lambda x: x.created_at, reverse=True)
        return jobs[:limit]
