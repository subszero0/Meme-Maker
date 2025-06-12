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
        print("❌ Both Redis and FakeRedis unavailable. Installing FakeRedis...")
        import subprocess
        subprocess.run(["poetry", "add", "--group", "dev", "fakeredis"], check=True)
        import fakeredis
        redis = fakeredis.FakeRedis()
        print("✅ Installed and using FakeRedis for local development")

# Initialize RQ queue for video clipping jobs
q = Queue("clips", connection=redis)
