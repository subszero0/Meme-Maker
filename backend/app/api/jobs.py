import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, status
from decimal import Decimal

from ..models import JobCreate, JobResponse, JobStatus, Job
from .. import redis, q
from ..metrics import clip_jobs_queued_total

router = APIRouter()


@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(job_data: JobCreate) -> JobResponse:
    """Create a new video clipping job"""
    # Validate clip duration (max 3 minutes = 180 seconds)
    duration = job_data.out_ts - job_data.in_ts
    if duration <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="out_ts must be greater than in_ts"
        )
    
    if duration > 180:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Clip duration cannot exceed 180 seconds (3 minutes)"
        )
    
    # Generate job ID
    job_id = uuid.uuid4().hex
    
    # Create job object
    job = Job(
        id=job_id,
        url=job_data.url,
        in_ts=Decimal(str(job_data.in_ts)),
        out_ts=Decimal(str(job_data.out_ts)),
        status=JobStatus.queued,
        created_at=datetime.utcnow()
    )
    
    # Store job in Redis hash
    job_dict = job.dict()
    # Convert Decimal and datetime values to strings for Redis storage
    for key, value in job_dict.items():
        if isinstance(value, Decimal):
            job_dict[key] = str(value)
        elif isinstance(value, datetime):
            job_dict[key] = value.isoformat() + "Z"
        elif value is None:
            job_dict[key] = "None"
    redis.hset(f"job:{job_id}", mapping=job_dict)
    
    # Enqueue RQ job with new process_clip function
    try:
        q.enqueue(
            "worker.process_clip.process_clip",
            job_id,
            str(job_data.url),
            float(job.in_ts),
            float(job.out_ts),
            job_timeout="5m"
        )
        
        # Increment queued jobs counter
        clip_jobs_queued_total.inc()
        
    except Exception as e:
        # Clean up job from Redis if enqueueing fails
        redis.delete(f"job:{job_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enqueue job: {str(e)}"
        )
    
    return JobResponse(
        id=job_id,
        status=JobStatus.queued,
        created_at=job.created_at
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str) -> JobResponse:
    """Get job status and download URL if ready"""
    # Look up job in Redis
    job_data = redis.hgetall(f"job:{job_id}")
    
    if not job_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Parse job data from Redis
    try:
        # Redis returns bytes, need to decode
        decoded_data = {k.decode(): v.decode() for k, v in job_data.items()}
        
        # Convert back to proper types for Job model
        parsed_data = {}
        for key, value in decoded_data.items():
            if key in ['in_ts', 'out_ts']:
                parsed_data[key] = Decimal(value)
            elif key == 'created_at':
                parsed_data[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
            elif key in ['progress', 'error_code']:
                parsed_data[key] = None if value == 'None' else (int(value) if key == 'progress' and value else value)
            else:
                parsed_data[key] = value
        
        job = Job.parse_obj(parsed_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse job data: {str(e)}"
        )
    
    # Build response based on status
    response = JobResponse(
        id=job.id,
        status=job.status,
        created_at=job.created_at,
    )
    
    # Include progress for queued/working jobs
    if job.status in {JobStatus.queued, JobStatus.working}:
        response.progress = job.progress
    
    # Include download URL for completed jobs
    if job.status == JobStatus.done:
        # Get presigned URL from job data
        response.url = decoded_data.get('url')
        
        # Set TTL for job cleanup (1 hour)
        redis.expire(f"job:{job_id}", 3600)
    
    # Include error code for failed jobs
    if job.status == JobStatus.error:
        response.error_code = job.error_code
        # Set TTL for error job cleanup (1 hour)
        redis.expire(f"job:{job_id}", 3600)
    
    return response 