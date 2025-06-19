"""
Queue manager for handling job processing queue.
Simplified version for testing configuration.
"""
from typing import List
from ..models import Job


class QueueManager:
    """Simplified queue manager for testing"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._queue = []  # In-memory queue for testing
    
    async def enqueue_job(self, job: Job) -> None:
        """Add job to queue"""
        self._queue.append(job.id)
    
    async def get_queue_size(self) -> int:
        """Get current queue size"""
        return len(self._queue)
    
    async def remove_job(self, job_id: str) -> bool:
        """Remove job from queue"""
        try:
            self._queue.remove(job_id)
            return True
        except ValueError:
            return False 