"""RQ Queue depth metrics updater"""

import asyncio
import logging
import os
from redis import Redis
from rq import Queue

from ..metrics_definitions import QUEUE_DEPTH, METRICS_AVAILABLE

logger = logging.getLogger(__name__)

# Redis connection
redis_url = os.environ.get('REDIS_URL', 'redis://redis:6379')

async def update_queue_metrics():
    """Update RQ queue depth metrics every 5 seconds"""
    if not METRICS_AVAILABLE:
        logger.warning("Metrics not available, skipping queue depth updates")
        return
    
    try:
        redis_client = Redis.from_url(redis_url)
        queue = Queue("clips", connection=redis_client)
        
        while True:
            try:
                queue_depth = len(queue)
                QUEUE_DEPTH.set(queue_depth)
                logger.debug(f"Updated queue depth metric: {queue_depth}")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error updating queue metrics: {e}")
                await asyncio.sleep(10)  # Wait longer on error
                
    except Exception as e:
        logger.error(f"Failed to initialize queue metrics updater: {e}")

def start_queue_metrics_updater():
    """Start the queue metrics updater task"""
    if METRICS_AVAILABLE:
        # Create task to run in background
        asyncio.create_task(update_queue_metrics())
        logger.info("Started RQ queue metrics updater")
    else:
        logger.warning("Metrics not available, not starting queue updater") 