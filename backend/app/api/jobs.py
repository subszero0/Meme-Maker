import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import asyncio

from fastapi import APIRouter, HTTPException, status
from decimal import Decimal

from ..models import JobCreate, JobResponse, JobStatus, Job
from .. import redis, q
from ..metrics import clip_jobs_queued_total

router = APIRouter()

# NOTE: Job simulation disabled - always use real worker for proper testing
# Real worker processing provides actual video files and tests the full pipeline

@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(job_data: JobCreate) -> JobResponse:
    """Create a new video clipping job"""
    print(f"🏗️  Backend: Received job creation request: {job_data.dict()}")
    print(f"🏗️  Backend: format_id received: {job_data.format_id}")
    
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
    print(f"🏗️  Backend: Generated job ID: {job_id}")
    
    # Create job object with format_id
    job = Job(
        id=job_id,
        url=job_data.url,
        in_ts=Decimal(str(job_data.in_ts)),
        out_ts=Decimal(str(job_data.out_ts)),
        status=JobStatus.queued,
        created_at=datetime.utcnow(),
        format_id=job_data.format_id  # Store the selected format ID
    )
    
    print(f"🏗️  Backend: Created job object with format_id: {job.format_id}")
    
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
    
    print(f"🏗️  Backend: Storing job in Redis with format_id: {job_dict.get('format_id')}")
    redis.hset(f"job:{job_id}", mapping=job_dict)
    
    # Enqueue RQ job with real worker processing including format_id
    try:
        # Always use real worker for proper testing and functionality
        print(f"🚀 Backend: Enqueueing job {job_id} to worker for processing with format: {job_data.format_id}")
        print(f"🚀 Backend: Worker arguments: job_id={job_id}, url={job_data.url}, in_ts={float(job.in_ts)}, out_ts={float(job.out_ts)}, format_id={job_data.format_id}")
        
        q.enqueue(
            "worker.process_clip.process_clip",
            job_id,
            str(job_data.url),
            float(job.in_ts),
            float(job.out_ts),
            job_data.format_id,  # Pass format_id to worker
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
    
    response = JobResponse(
        id=job_id,
        status=JobStatus.queued,
        created_at=job.created_at,
        format_id=job.format_id
    )
    
    print(f"🏗️  Backend: Returning response with format_id: {response.format_id}")
    return response


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str) -> JobResponse:
    """Get job status and download URL if ready"""
    print(f"🔍 Backend: Getting job status for {job_id}")
    
    # Look up job in Redis
    job_data = redis.hgetall(f"job:{job_id}")
    
    if not job_data:
        print(f"❌ Backend: Job {job_id} not found in Redis")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    print(f"🔍 Backend: Raw job data from Redis: {job_data}")
    
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
            elif key in ['progress', 'error_code', 'download_url', 'stage', 'format_id', 'video_title']:
                parsed_data[key] = None if value == 'None' else (int(value) if key == 'progress' and value else value)
            else:
                parsed_data[key] = value
        
        job = Job.parse_obj(parsed_data)
        print(f"🔍 Backend: Parsed job object - Status: {job.status}, Progress: {job.progress}, Stage: {job.stage}")
        print(f"🔍 Backend: Job format_id: {job.format_id}, Download URL: {job.download_url}")
    except Exception as e:
        print(f"❌ Backend: Failed to parse job data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse job data: {str(e)}"
        )
    
    # Build response based on status
    response = JobResponse(
        id=job.id,
        status=job.status,
        created_at=job.created_at,
        format_id=job.format_id,
        video_title=job.video_title
    )
    
    print(f"🔍 Backend: Building response for status: {job.status}")
    
    # Include progress and stage for queued/working jobs
    if job.status in {JobStatus.queued, JobStatus.working}:
        response.progress = job.progress
        response.stage = job.stage
        print(f"🔍 Backend: In-progress job - Progress: {response.progress}%, Stage: {response.stage}")
    
    # Include download URL for completed jobs
    if job.status == JobStatus.done:
        # Get presigned URL from job data
        response.download_url = job.download_url
        print(f"✅ Backend: Job completed - Download URL: {response.download_url}")
        
        # Set TTL for job cleanup (1 hour)
        redis.expire(f"job:{job_id}", 3600)
    
    # Include error code for failed jobs
    if job.status == JobStatus.error:
        response.error_code = job.error_code
        print(f"❌ Backend: Job failed - Error code: {response.error_code}")
        # Set TTL for error job cleanup (1 hour)
        redis.expire(f"job:{job_id}", 3600)
    
    print(f"🔍 Backend: Returning response for job {job_id}: {response.dict()}")
    return response 