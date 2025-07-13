from rq import Queue

from app.storage import LocalStorageManager
from app.storage_factory import storage_manager

from . import redis as redis_client


def get_storage() -> LocalStorageManager:
    """FastAPI dependency for storage manager"""
    return storage_manager


def get_redis():
    """FastAPI dependency for sync Redis client (for RQ)"""
    from . import init_redis, redis

    # Ensure Redis is initialized
    if redis is None:
        print("🔧 Initializing Redis from dependency...")
        try:
            init_redis()
            from . import redis  # Re-import after initialization

            print(f"🔧 Redis initialized: {type(redis)}")
        except Exception as e:
            print(f"❌ Redis initialization failed: {e}")
            return None

    return redis


async def get_async_redis():
    """FastAPI dependency for async Redis client (for cache)"""
    from . import get_async_redis_client, init_redis

    print("🔍 Getting async Redis client...")

    # Ensure Redis is initialized
    try:
        init_redis()
        client = await get_async_redis_client()
        if client is None:
            print("⚠️ Async Redis client not available")
            return None

        print(f"✅ Async Redis client ready: {type(client)}")

        # Test the client to ensure it's working
        try:
            await client.ping()
            print("✅ Async Redis client ping successful")
        except Exception as ping_error:
            print(f"⚠️ Async Redis client ping failed: {ping_error}")
            # Still return the client as it might work for other operations

        return client
    except Exception as e:
        print(f"❌ Async Redis client initialization failed: {e}")
        return None


def get_redis_client():
    """FastAPI dependency for Redis client (alias for phase3 compatibility)"""
    return get_redis()


def get_job_repository():
    """FastAPI dependency for job repository"""
    from .repositories.job_repository import JobRepository

    return JobRepository()


def get_clips_queue() -> Queue:
    """
    Returns a Redis Queue instance for the 'clips' queue.
    """
    redis_connection = get_redis()
    return Queue("clips", connection=redis_connection)
