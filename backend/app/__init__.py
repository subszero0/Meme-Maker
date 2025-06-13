import os
from redis import Redis
from rq import Queue

from .config import settings

# For local development, use FakeRedis if Redis is unavailable
try:
    # Try to connect to real Redis
    redis = Redis.from_url(settings.redis_url)
    redis.ping()  # Test connection
    print(f"✅ Connected to Redis at {settings.redis_url}")
except Exception as e:
    # Fall back to FakeRedis for local development
    try:
        import fakeredis
        redis = fakeredis.FakeRedis()
        print(f"⚠️  Using FakeRedis for local development (Redis unavailable: {e})")
    except ImportError:
        print("❌ Both Redis and FakeRedis unavailable")
        raise Exception("Redis connection failed and FakeRedis not available. Please install FakeRedis or ensure Redis is running.")

# Initialize RQ queue for video clipping jobs
q = Queue("clips", connection=redis)
