import time
import logging
from redis import Redis
from rq import Queue

from .config import settings

logger = logging.getLogger(__name__)

def connect_to_redis(retries: int = 5, delay: int = 2) -> Redis:
    """Connect to Redis with retry logic"""
    for attempt in range(retries):
        try:
            redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
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
                logger.error("Unable to connect to Redis after multiple attempts")
                raise Exception("Unable to connect to Redis after multiple attempts") from e

# Initialize Redis connection with retry logic
redis = connect_to_redis()

# Initialize RQ queue for video clipping jobs
q = Queue("clips", connection=redis)
