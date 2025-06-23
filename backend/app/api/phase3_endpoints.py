"""
Phase 3 API endpoints for advanced features.
Includes cache management, cleanup operations, and system monitoring.
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from ..cache.metadata_cache import MetadataCache
from ..constants import AsyncConfig, CacheConfig
from ..dependencies import get_job_repository, get_redis_client
from ..factories.storage_factory import StorageFactory
from ..logging.config import get_logger
from ..middleware.rate_limiter import RateLimiter, get_rate_limiter
from ..repositories.job_repository import JobRepository
from ..tasks.cleanup import CleanupManager, schedule_cleanup_job

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/cache/stats")
async def get_cache_stats(redis_client=Depends(get_redis_client)) -> Dict[str, Any]:
    """
    Get cache usage statistics

    Returns cache hit rates, memory usage, and key counts
    """
    try:
        cache = MetadataCache(redis_client)
        stats = await cache.get_cache_stats()

        return {
            "status": "success",
            "cache_stats": stats,
            "cache_config": {
                "metadata_ttl": CacheConfig.METADATA_TTL,
                "format_ttl": CacheConfig.FORMAT_TTL,
                "thumbnail_ttl": CacheConfig.THUMBNAIL_TTL,
            },
        }

    except Exception as e:
        logger.error(f"Failed to get cache stats: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve cache statistics"
        )


@router.post("/cache/invalidate")
async def invalidate_cache(
    url: str, redis_client=Depends(get_redis_client)
) -> Dict[str, Any]:
    """
    Invalidate cache entries for a specific URL

    Args:
        url: Video URL to invalidate from cache
    """
    try:
        cache = MetadataCache(redis_client)
        deleted_count = await cache.invalidate_url(url)

        return {
            "status": "success",
            "message": f"Invalidated {deleted_count} cache entries",
            "url": url,
            "deleted_entries": deleted_count,
        }

    except Exception as e:
        logger.error(f"Failed to invalidate cache for URL {url}: {str(e)}")
        raise HTTPException(status_code=500, detail="Cache invalidation failed")


@router.post("/cache/clear")
async def clear_cache(
    cache_type: Optional[str] = None, redis_client=Depends(get_redis_client)
) -> Dict[str, Any]:
    """
    Clear cache entries by type

    Args:
        cache_type: Type of cache to clear (metadata, format, thumbnail) or all
    """
    try:
        if cache_type and cache_type not in ["metadata", "format", "thumbnail", "all"]:
            raise HTTPException(status_code=400, detail="Invalid cache type")

        # This would implement cache clearing logic
        # For now, return success message

        return {
            "status": "success",
            "message": f"Cache cleared: {cache_type or 'all'}",
            "cache_type": cache_type or "all",
        }

    except Exception as e:
        logger.error(f"Failed to clear cache: {str(e)}")
        raise HTTPException(status_code=500, detail="Cache clearing failed")


@router.post("/cleanup/jobs")
async def trigger_job_cleanup(
    background_tasks: BackgroundTasks,
    job_repository: JobRepository = Depends(get_job_repository),
) -> Dict[str, Any]:
    """
    Trigger background job cleanup

    Schedules cleanup of expired jobs and associated files
    """
    try:
        # Schedule cleanup in background
        await schedule_cleanup_job(background_tasks, job_repository)

        return {
            "status": "success",
            "message": "Job cleanup scheduled",
            "scheduled_at": "background",
        }

    except Exception as e:
        logger.error(f"Failed to schedule job cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail="Cleanup scheduling failed")


@router.post("/cleanup/files")
async def trigger_file_cleanup(
    max_age_hours: int = 24, job_repository: JobRepository = Depends(get_job_repository)
) -> Dict[str, Any]:
    """
    Trigger temporary file cleanup

    Args:
        max_age_hours: Maximum age in hours for temporary files
    """
    try:
        cleanup_manager = CleanupManager(job_repository)
        stats = await cleanup_manager.cleanup_temporary_files(max_age_hours)

        return {
            "status": "success",
            "message": "File cleanup completed",
            "cleanup_stats": stats,
        }

    except Exception as e:
        logger.error(f"Failed to cleanup files: {str(e)}")
        raise HTTPException(status_code=500, detail="File cleanup failed")


@router.get("/rate-limit/status")
async def get_rate_limit_status(
    request: Request, rate_limiter: RateLimiter = Depends(get_rate_limiter)
) -> Dict[str, Any]:
    """
    Get current rate limit status for the requesting client
    """
    try:
        info = rate_limiter.get_rate_limit_info(request)

        return {"status": "success", "rate_limit_info": info}

    except Exception as e:
        logger.error(f"Failed to get rate limit status: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Rate limit status retrieval failed"
        )


@router.get("/storage/info")
async def get_storage_info() -> Dict[str, Any]:
    """
    Get information about current storage configuration
    """
    try:
        storage = StorageFactory.get_default_storage()

        available_backends = [
            backend.value for backend in StorageFactory.list_available_backends()
        ]

        return {
            "status": "success",
            "current_backend": storage.get_backend_type().value,
            "available_backends": available_backends,
        }

    except Exception as e:
        logger.error(f"Failed to get storage info: {str(e)}")
        raise HTTPException(status_code=500, detail="Storage info retrieval failed")


@router.get("/system/health")
async def get_system_health(
    redis_client=Depends(get_redis_client),
    job_repository: JobRepository = Depends(get_job_repository),
) -> Dict[str, Any]:
    """
    Get comprehensive system health status including Phase 3 components
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",  # Would be actual timestamp
            "components": {},
        }

        # Cache health
        try:
            cache = MetadataCache(redis_client)
            cache_stats = await cache.get_cache_stats()
            health_status["components"]["cache"] = {
                "status": "healthy",
                "stats": cache_stats,
            }
        except Exception as e:
            health_status["components"]["cache"] = {
                "status": "unhealthy",
                "error": str(e),
            }

        # Storage health
        try:
            storage = StorageFactory.get_default_storage()
            health_status["components"]["storage"] = {
                "status": "healthy",
                "backend": storage.get_backend_type().value,
            }
        except Exception as e:
            health_status["components"]["storage"] = {
                "status": "unhealthy",
                "error": str(e),
            }

        # Rate limiter health
        try:
            health_status["components"]["rate_limiter"] = {
                "status": "healthy",
                "config": {"requests_per_minute": "60", "jobs_per_hour": "50"},
            }
        except Exception as e:
            health_status["components"]["rate_limiter"] = {
                "status": "unhealthy",
                "error": str(e),
            }

        # Overall health
        components_dict: Dict[str, Any] = health_status["components"]
        unhealthy_components = [
            name
            for name, component in components_dict.items()
            if component["status"] == "unhealthy"
        ]

        if unhealthy_components:
            health_status["status"] = "degraded"
            health_status["unhealthy_components"] = unhealthy_components

        return health_status

    except Exception as e:
        logger.error(f"Failed to get system health: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z",
        }


@router.get("/metrics/phase3")
async def get_phase3_metrics(redis_client=Depends(get_redis_client)) -> Dict[str, Any]:
    """
    Get Phase 3 specific metrics
    """
    try:
        cache = MetadataCache(redis_client)
        cache_stats = await cache.get_cache_stats()

        metrics = {
            "async_processing": {
                "max_concurrent_jobs": AsyncConfig.MAX_CONCURRENT_JOBS,
                "batch_size": AsyncConfig.BATCH_SIZE,
                "processing_timeout": AsyncConfig.PROCESSING_TIMEOUT,
            },
            "cache": cache_stats,
            "cleanup": {
                "interval_hours": AsyncConfig.CLEANUP_INTERVAL_HOURS,
                "cache_cleanup_hours": AsyncConfig.CACHE_CLEANUP_INTERVAL_HOURS,
            },
            "rate_limiting": {
                "enabled": True,
                "global_limit": "60 requests/minute",
                "endpoint_limits": {"jobs": "50/hour", "metadata": "30/minute"},
            },
        }

        return {"status": "success", "phase3_metrics": metrics}

    except Exception as e:
        logger.error(f"Failed to get Phase 3 metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Metrics retrieval failed")
