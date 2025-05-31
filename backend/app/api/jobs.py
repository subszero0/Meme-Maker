import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, status, Depends
from decimal import Decimal
from fastapi import Request  # For rate limiting
from fastapi.responses import JSONResponse
import logging

from ..models import JobCreate, JobResponse, JobStatus, Job, ClipJob
from .. import redis, q
from ..metrics import clip_jobs_queued_total
from ..utils import get_storage
from ..ratelimit import global_limiter, job_creation_limiter
from ..config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# RQ queue setup
from rq import Queue

try:
    job_queue = Queue('clip_jobs', connection=redis)
except Exception as e:
    logger.error(f"Failed to initialize job queue: {e}")
    job_queue = None


@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED, 
             dependencies=[Depends(global_limiter), Depends(job_creation_limiter)])
async def create_job(job_data: JobCreate) -> JobResponse:
    """Create a new video clipping job
    
    Rate limits:
    - Global: 10 requests per minute per IP
    - Job creation: 3 jobs per hour per IP
    """
    # Validate terms acceptance
    if not job_data.accepted_terms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must accept the Terms of Use to proceed."
        )
    
    try:
        # Convert time strings to seconds and validate
        start_seconds = job_data.start_seconds
        end_seconds = job_data.end_seconds
        duration = end_seconds - start_seconds
        
        if duration <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="end time must be greater than start time"
            )
        
        if duration > 180:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Clip duration cannot exceed 180 seconds (3 minutes)"
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid time format: {str(e)}"
        )
    
    # Generate job ID
    job_id = uuid.uuid4().hex
    
    # Create job object for Redis storage
    job = Job(
        id=job_id,
        url=job_data.url,
        in_ts=Decimal(str(start_seconds)),
        out_ts=Decimal(str(end_seconds)),
        status=JobStatus.queued,
        created_at=datetime.utcnow()
    )
    
    # Store job in Redis hash
    job_dict = job.model_dump()
    # Convert all values to Redis-compatible types
    redis_data = {}
    for key, value in job_dict.items():
        if isinstance(value, Decimal):
            redis_data[key] = str(value)
        elif isinstance(value, datetime):
            redis_data[key] = value.isoformat() + "Z"
        elif value is None:
            redis_data[key] = "None"
        elif hasattr(value, 'value'):  # Handle enum types
            redis_data[key] = value.value
        else:
            # Convert any remaining non-string types to string
            redis_data[key] = str(value)
    redis.hset(f"job:{job_id}", mapping=redis_data)
    
    # Enqueue RQ job with individual parameters instead of dataclass
    try:
        q.enqueue(
            "clip_processor.process_clip",
            job_id,
            str(job_data.url),
            start_seconds,
            end_seconds,
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
        job_id=job_id,
        status=JobStatus.queued,
        created_at=job.created_at
    )


@router.get("/jobs/{job_id}", response_model=JobResponse, dependencies=[Depends(global_limiter)])
async def get_job(job_id: str) -> JobResponse:
    """Get job status and download URL if ready
    
    Rate limits:
    - Global: 10 requests per minute per IP
    """
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
        
        job = Job.model_validate(parsed_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse job data: {str(e)}"
        )
    
    # Build response based on status
    response = JobResponse(
        job_id=job.id,
        status=job.status,
        created_at=job.created_at,
    )
    
    # Include progress for queued/working jobs
    if job.status in {JobStatus.queued, JobStatus.working}:
        response.progress = job.progress
    
    # Include download URL for completed jobs
    if job.status == JobStatus.done:
        # Get object key from job data or generate presigned URL
        object_key = decoded_data.get('object_key')
        if object_key:
            try:
                response.link = get_storage().generate_presigned_url(object_key, expiration=3600)
            except Exception as e:
                # If presigned URL generation fails, mark job as error
                redis.hset(f"job:{job_id}", mapping={
                    "status": JobStatus.error.value,
                    "error_code": "PRESIGN_FAIL"
                })
                response.status = JobStatus.error
                response.error_code = "PRESIGN_FAIL"
        
        # Set TTL for job cleanup (1 hour)
        redis.expire(f"job:{job_id}", 3600)
    
    # Include error code for failed jobs
    if job.status == JobStatus.error:
        response.error_code = job.error_code
        # Set TTL for error job cleanup (1 hour)
        redis.expire(f"job:{job_id}", 3600)
    
    return response 