import logging
import os
import time
from typing import Optional

from redis import Redis
from rq import Queue

from .config import settings

logger = logging.getLogger(__name__)


def connect_to_redis(
    retries: int = 5, delay: int = 2, required: bool = True
) -> Optional[Redis]:  # type: ignore
    """Connect to Redis with retry logic"""
    # Check if we're in a test environment
    if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TESTING"):
        logger.info("Test environment detected, skipping Redis connection")
        return None

    for attempt in range(retries):
        try:
            redis_client = Redis.from_url(
                settings.redis_url
            )  # Removed decode_responses=True
            # Test the connection
            redis_client.ping()
            logger.info("Redis connection successful")
            return redis_client
        except Exception as e:
            logger.warning(f"Redis connection attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                if required:
                    logger.error("Unable to connect to Redis after multiple attempts")
                    raise Exception(
                        "Unable to connect to Redis after multiple attempts"
                    ) from e
                else:
                    logger.warning("Redis connection failed, but not required")
                    return None

    # This should never be reached, but add for completeness
    return None


# Initialize Redis connection with retry logic (optional for tests)
redis = connect_to_redis(required=False)

# Initialize RQ queue for video clipping jobs (only if Redis is available)
q = Queue("clips", connection=redis) if redis else None
