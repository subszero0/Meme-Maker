from fastapi import Depends
from app.storage_factory import get_storage_manager, storage_manager
from app.storage import LocalStorageManager
from typing import Optional


def get_storage() -> LocalStorageManager:
    """FastAPI dependency for storage manager"""
    return storage_manager


def get_redis():
    """FastAPI dependency for sync Redis client (for RQ)"""
    from . import redis, init_redis
    
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
            print(f"✅ Async Redis client ping successful")
        except Exception as ping_error:
            print(f"⚠️ Async Redis client ping failed: {ping_error}")
            # Still return the client as it might work for other operations
        
        return client
    except Exception as e:
        print(f"❌ Async Redis client initialization failed: {e}")
        return None


 