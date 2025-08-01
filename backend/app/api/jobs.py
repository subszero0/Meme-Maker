import logging
import uuid
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl, validator
from rq import Queue

# Import settings using direct file path to avoid package/module conflict
# Import settings from the new configuration module
from app.config.configuration import get_settings
from app.dependencies import get_clips_queue, get_redis, get_storage
from app.models import Job, JobResponse, JobStatus
from app.storage import LocalStorageManager

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
        if (
            "in_ts" in values and (v - values["in_ts"]) > 60
        ):  # 1 minute max for T-003 protection
            raise ValueError(
                "Clip duration cannot exceed 1 minute (T-003 DoS protection)"
            )
        return v


@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    request: JobCreateRequest,
    redis=Depends(get_redis),
    clips_queue: Queue = Depends(get_clips_queue),
):
    """Create a new video processing job"""

    if not redis:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis service unavailable",
        )

    # Check queue capacity with T-003 protection
    queue_length = redis.llen("rq:queue:default")
    if queue_length >= 15:  # T-003 reduced limit
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Queue at capacity. T-003 DoS protection active. Try again later.",
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
        status=JobStatus.queued,
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

    # FIXED: Queue job for processing using RQ
    # Convert Decimal to float for worker compatibility
    clips_queue.enqueue(
        "worker.process_clip.process_clip",
        job_id=job.id,
        url=str(job.url),
        in_ts=(
            float(job.in_ts) if job.in_ts is not None else 0.0
        ),  # Convert Decimal to float
        out_ts=(
            float(job.out_ts) if job.out_ts is not None else 0.0
        ),  # Convert Decimal to float
        resolution=job.format_id,  # Use 'resolution' parameter name that worker expects
        job_timeout="2h",
        result_ttl=86400,  # Keep result for 1 day
    )

    logger.info(f"Created and queued job {job_id} for URL: {request.url}")

    return JobResponse(
        id=job.id, status=job.status, created_at=job.created_at, format_id=job.format_id
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, redis=Depends(get_redis)):
    """Get job status and details"""

    if not redis:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis service unavailable",
        )

    job_key = f"job:{job_id}"
    job_data = redis.hgetall(job_key)

    if not job_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    # Decode Redis bytes to strings if needed
    job_data = {
        (k.decode() if isinstance(k, bytes) else k): (
            v.decode() if isinstance(v, bytes) else v
        )
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
        format_id=(
            job_data.get("format_id") if job_data.get("format_id") != "" else None
        ),
        video_title=job_data.get("video_title"),
    )


@router.get("/jobs/{job_id}/download")
async def download_job_file(
    job_id: str,
    storage: LocalStorageManager = Depends(get_storage),
    redis=Depends(get_redis),
):
    """Download processed video file with integrity checks"""

    if not redis:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis service unavailable",
        )

    # Get job data from Redis
    job_key = f"job:{job_id}"
    job_data = redis.hgetall(job_key)

    if not job_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    # Decode Redis data if needed
    job_data = {
        (k.decode() if isinstance(k, bytes) else k): (
            v.decode() if isinstance(v, bytes) else v
        )
        for k, v in job_data.items()
    }

    # Check if job is completed
    if job_data.get("status") != JobStatus.done.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Job not completed yet"
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
                    logger.error(
                        f"File size mismatch for {job_id}: expected {expected_size}, got {actual_size}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="File integrity check failed",
                    )

            video_title = job_data.get("video_title", "video")

            # --- Robust filename handling ---
            import unicodedata
            import urllib.parse

            raw_filename = f"{video_title}_{job_id}.mp4"

            # ASCII-only fallback for `filename` (required by RFC6266)
            ascii_filename = (
                unicodedata.normalize("NFKD", raw_filename)
                .encode("ascii", "ignore")
                .decode("ascii")
            ) or "clip.mp4"

            # RFC 5987 encoded value for full UTF-8 support
            quoted_filename = urllib.parse.quote(raw_filename.encode("utf-8"))

            # Build Content-Disposition combining ASCII fallback and RFC5987 UTF-8 value
            content_disposition = f"attachment; filename=\"{ascii_filename}\"; filename*=UTF-8''{quoted_filename}"

            return FileResponse(
                path=str(file_path),
                media_type="video/mp4",
                filename=ascii_filename,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Content-Disposition": content_disposition,
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
            )

    except FileNotFoundError:
        pass

    # If we get here, file wasn't found in either storage
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="File not found or expired"
    )


@router.delete("/jobs/{job_id}")
async def cleanup_job(
    job_id: str,
    storage: LocalStorageManager = Depends(get_storage),
    redis=Depends(get_redis),
):
    """Clean up job data and associated files"""

    # Delete file from storage
    deleted = await storage.delete(job_id)

    # Delete job data from Redis
    job_key = f"job:{job_id}"
    redis.delete(job_key)

    return {"message": "Job cleaned up successfully", "file_deleted": deleted}


@router.get("/storage/stats")
async def get_storage_stats(storage: LocalStorageManager = Depends(get_storage)):
    """Get storage usage statistics (admin endpoint)"""
    return storage.get_storage_stats()
