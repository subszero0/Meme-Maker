from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, HttpUrl, Field, validator
from decimal import Decimal


class JobStatus(str, Enum):
    """Job status enumeration"""
    queued = "queued"
    working = "working"
    done = "done"
    error = "error"


class Job(BaseModel):
    """Core job model for Redis storage"""
    id: str
    url: HttpUrl  # Original source URL (YouTube, etc.)
    in_ts: Decimal = Field(gt=0)  # seconds
    out_ts: Decimal = Field(gt=0)  # seconds
    status: JobStatus = JobStatus.queued
    progress: Optional[int] = None
    error_code: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    download_url: Optional[str] = None  # Presigned S3 URL when done - no validation needed
    stage: Optional[str] = None  # Current processing stage description
    
    @validator('download_url', 'stage', pre=True)
    def validate_optional_fields(cls, v):
        # Allow any string for download URLs and stages (including localhost, minio, etc.)
        if v == "None":
            return None
        return v


class JobCreate(BaseModel):
    """Request model for creating a new job"""
    url: HttpUrl
    in_ts: float  # seconds
    out_ts: float  # seconds


class JobResponse(BaseModel):
    """Response model for job operations"""
    id: str
    status: JobStatus
    created_at: datetime
    progress: Optional[int] = None
    download_url: Optional[str] = None  # presigned S3 URL when done
    error_code: Optional[str] = None
    stage: Optional[str] = None  # Current processing stage description


class MetadataRequest(BaseModel):
    """Request model for fetching video metadata"""
    url: HttpUrl


class MetadataResponse(BaseModel):
    """Response model for video metadata"""
    title: str
    duration: float  # seconds
    thumbnail_url: Optional[str] = None
    resolutions: list[str] = []


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str 