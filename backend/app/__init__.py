"""
Application initialization module.
Initialize Redis and queue connections.
"""

# Import settings for backward compatibility with worker

# Import settings from the new configuration module
from app.config.configuration import get_settings

settings = get_settings()

# Defer Redis initialization to avoid import errors during testing
redis = None  # Sync Redis client for RQ
async_redis_pool = None  # Async Redis connection pool
q = None


def init_redis():
    """Initialize Redis connection with comprehensive error handling"""
    global redis, async_redis_pool, q

    if redis is not None and async_redis_pool is not None:
        print(
            f"🔄 Redis already initialized: "
            f"sync={type(redis)}, async_pool={type(async_redis_pool)}"
        )
        return redis

    import os

    redis_url = os.getenv("REDIS_URL", settings.redis_url)
    print(f"🔍 Redis URL from env: {redis_url}")

    try:
        import redis.asyncio as aioredis
        from redis import Redis
        from rq import Queue

        # Try to connect to real Redis with more robust settings
        print(f"🔍 Attempting Redis connection to: {redis_url}")

        # Initialize sync Redis client for RQ
        redis = Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=10,
            socket_timeout=10,
            retry_on_timeout=True,
            health_check_interval=30,
        )

        # Test sync connection with retries
        for attempt in range(3):
            try:
                result = redis.ping()
                print(
                    f"✅ Sync Redis ping successful on attempt {attempt + 1}: {result}"
                )
                break
            except Exception as retry_e:
                if attempt == 2:  # Last attempt
                    raise retry_e
                print(f"⚠️ Redis ping failed attempt {attempt + 1}: {retry_e}")
                import time

                time.sleep(1)

        print(f"✅ Connected to sync Redis at {redis_url}")
        print(f"🔍 Redis info: {redis.info('server').get('redis_version', 'unknown')}")

        # Initialize async Redis connection pool
        print("🔍 Creating async Redis connection pool...")
        async_redis_pool = aioredis.ConnectionPool.from_url(
            redis_url,
            decode_responses=True,
            max_connections=20,
            retry_on_timeout=True,
            socket_connect_timeout=10,
            socket_timeout=10,
        )
        print("✅ Async Redis connection pool created successfully")

    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        # Fall back to FakeRedis for local development
        try:
            import fakeredis
            import fakeredis.aioredis

            redis = fakeredis.FakeRedis(decode_responses=True)
            async_redis_pool = "fake"  # Flag for fake Redis
            print(
                "⚠️  Using FakeRedis for local development - "
                "caching will work but won't persist"
            )
        except ImportError:
            print("❌ Both Redis and FakeRedis unavailable")
            redis = None
            async_redis_pool = None
            print("⚠️ Continuing without Redis - caching disabled")
            return None

    # Initialize RQ queue for video clipping jobs
    try:
        if redis is not None:
            q = Queue("clips", connection=redis)
            print("✅ Initialized RQ queue 'clips'")
    except Exception as e:
        print(f"⚠️ RQ queue initialization failed: {e}")
        q = None

    print(
        f"🎯 Redis initialization complete: "
        f"sync={type(redis)}, async_pool={type(async_redis_pool)}"
    )
    return redis


async def get_async_redis_client():
    """Get async Redis client for cache operations"""
    global async_redis_pool

    if async_redis_pool is None:
        print("⚠️ Async Redis pool not initialized, initializing now...")
        init_redis()
        if async_redis_pool is None:
            print("❌ Async Redis pool initialization failed")
            return None

    if async_redis_pool == "fake":
        # Return a fake async Redis client
        try:
            import fakeredis.aioredis

            client = fakeredis.aioredis.FakeRedis(decode_responses=True)
            print("🔄 Using FakeRedis async client")
            return client
        except ImportError:
            print("❌ fakeredis.aioredis not available")
            return None

    try:
        import redis.asyncio as aioredis

        # Create async Redis client from connection pool
        client = aioredis.Redis(connection_pool=async_redis_pool)
        print(f"✅ Created async Redis client from pool: {type(client)}")
        return client
    except Exception as e:
        print(f"❌ Failed to create async Redis client: {e}")
        return None
