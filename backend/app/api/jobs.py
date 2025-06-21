import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import asyncio

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl, validator
from decimal import Decimal
import redis as redis_client
import os
import logging
from pathlib import Path

from app.models import JobResponse, JobStatus, Job
from app.dependencies import get_storage, get_redis
from app.storage import LocalStorageManager
# Import settings using direct file path to avoid package/module conflict
# Import settings from the new configuration module
from app.config.configuration import get_settings
settings = get_settings()

router = APIRouter()
logger = logging.getLogger(__name__)

# NOTE: Job simulation disabled - always use real worker for proper testing
# Real worker processing provides actual video files and tests the full pipeline

# Job creation request model
class JobCreateRequest(BaseModel):
    url: HttpUrl
    in_ts: Decimal
    out_ts: Decimal
    format_id: Optional[str] = None
    
    @validator("in_ts", "out_ts")
    def validate_timestamps(cls, v):
        if v < 0:
            raise ValueError("Timestamps must be non-negative")
        return v
    
    @validator("out_ts")
    def validate_duration(cls, v, values):
        if "in_ts" in values and v <= values["in_ts"]:
            raise ValueError("End time must be greater than start time")
        if "in_ts" in values and (v - values["in_ts"]) > 180:  # 3 minutes max
            raise ValueError("Clip duration cannot exceed 3 minutes")
        return v

@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(request: JobCreateRequest, redis=Depends(get_redis)):
    """Create a new video processing job"""
    
    if not redis:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis service unavailable"
        )
    
    # Check queue capacity
    queue_length = redis.llen("rq:queue:default")
    if queue_length >= settings.max_concurrent_jobs:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Queue is full. Try again later."
        )
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Create job object
    job = Job(
        id=job_id,
        url=request.url,
        in_ts=request.in_ts,
        out_ts=request.out_ts,
        format_id=request.format_id,
        status=JobStatus.queued
    )
    
    # Store in Redis
    job_key = f"job:{job_id}"
    job_data = {
        "id": job.id,
        "url": str(job.url),
        "in_ts": str(job.in_ts),
        "out_ts": str(job.out_ts),
        "status": job.status.value,
        "created_at": job.created_at.isoformat(),
        "format_id": job.format_id or "",
    }
    
    redis.hset(job_key, mapping=job_data)
    redis.expire(job_key, 3600)  # 1 hour TTL
    
    # Job is now queued in Redis with status 'queued'
    # The worker will pick it up automatically from the polling loop
    # No need to use RQ enqueue since we have custom worker polling
    
    logger.info(f"Created job {job_id} for URL: {request.url}")
    
    return JobResponse(
        id=job.id,
        status=job.status,
        created_at=job.created_at,
        format_id=job.format_id
    )

@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, redis=Depends(get_redis)):
    """Get job status and details"""
    
    if not redis:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis service unavailable"
        )
    
    job_key = f"job:{job_id}"
    job_data = redis.hgetall(job_key)
    
    if not job_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Decode Redis bytes to strings if needed
    job_data = {
        (k.decode() if isinstance(k, bytes) else k): 
        (v.decode() if isinstance(v, bytes) else v) 
        for k, v in job_data.items()
    }
    
    return JobResponse(
        id=job_data["id"],
        status=JobStatus(job_data["status"]),
        created_at=job_data["created_at"],
        progress=int(job_data.get("progress", 0)),
        download_url=job_data.get("download_url"),
        error_code=job_data.get("error_code"),
        stage=job_data.get("stage"),
        format_id=job_data.get("format_id") if job_data.get("format_id") != "" else None,
        video_title=job_data.get("video_title")
    )

@router.get("/jobs/{job_id}/download")
async def download_job_file(
    job_id: str, 
    storage: LocalStorageManager = Depends(get_storage),
    redis=Depends(get_redis)
):
    """Download processed video file with integrity checks"""
    
    if not redis:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis service unavailable"
        )
    
    # Get job data from Redis
    job_key = f"job:{job_id}"
    job_data = redis.hgetall(job_key)
    
    if not job_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Decode Redis data if needed
    job_data = {
        (k.decode() if isinstance(k, bytes) else k): 
        (v.decode() if isinstance(v, bytes) else v) 
        for k, v in job_data.items()
    }
    
    # Check if job is completed
    if job_data.get("status") != JobStatus.done.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job not completed yet"
        )
    
    # Get file from local storage
    try:
        file_path = await storage.get(job_id)
        if file_path and file_path.exists():
            # Size check before serving
            expected_size = job_data.get("file_size")
            if expected_size:
                actual_size = file_path.stat().st_size
                if actual_size != int(expected_size):
                    logger.error(f"File size mismatch for {job_id}: expected {expected_size}, got {actual_size}")
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="File integrity check failed"
                    )
            
            video_title = job_data.get("video_title", "video")
            filename = f"{video_title}_{job_id}.mp4"
            
            return FileResponse(
                path=str(file_path),
                media_type="video/mp4",
                filename=filename,
                headers={
                    "Content-Disposition": f"attachment; filename=\"{filename}\"",
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
    
    except FileNotFoundError:
        pass
    
    # If we get here, file wasn't found in either storage
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="File not found or expired"
    )

@router.delete("/jobs/{job_id}")
async def cleanup_job(
    job_id: str,
    storage: LocalStorageManager = Depends(get_storage)
):
    """Clean up job data and associated files"""
    
    # Delete file from storage
    deleted = await storage.delete(job_id)
    
    # Delete job data from Redis
    job_key = f"job:{job_id}"
    redis.delete(job_key)
    
    return {
        "message": "Job cleaned up successfully",
        "file_deleted": deleted
    }

@router.get("/storage/stats")
async def get_storage_stats(
    storage: LocalStorageManager = Depends(get_storage)
):
    """Get storage usage statistics (admin endpoint)"""
    return storage.get_storage_stats() 