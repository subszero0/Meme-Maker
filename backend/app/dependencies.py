from fastapi import Depends
from app.storage_factory import get_storage_manager, storage_manager
from app.storage import LocalStorageManager, S3StorageManager
from typing import Union


def get_storage() -> Union[LocalStorageManager, S3StorageManager]:
    """FastAPI dependency for storage manager"""
    return storage_manager


def get_redis():
    """FastAPI dependency for Redis client"""
    from app import redis
    return redis 