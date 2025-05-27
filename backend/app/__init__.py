from redis import Redis
from rq import Queue

from .config import settings

# Initialize Redis connection
redis = Redis.from_url(settings.redis_url)

# Initialize RQ queue for video clipping jobs
q = Queue("clips", connection=redis)
