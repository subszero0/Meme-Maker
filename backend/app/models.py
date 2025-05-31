from datetime import datetime
from enum import Enum
from typing import Optional, Union
from pydantic import BaseModel, HttpUrl, Field, validator
from decimal import Decimal
from dataclasses import dataclass
import os


class JobStatus(str, Enum):
    """Job status enumeration"""
    queued = "queued"
    working = "working"
    done = "done"
    error = "error"


@dataclass
class ClipJob:
    """Dataclass for clip job data passed to RQ worker"""
    job_id: str
    url: str
    start_seconds: float
    end_seconds: float
    
    def duration(self) -> float:
        """Calculate clip duration in seconds"""
        return self.end_seconds - self.start_seconds


class Job(BaseModel):
    """Core job model for Redis storage"""
    id: str
    url: HttpUrl
    in_ts: Decimal = Field(gt=0)  # seconds
    out_ts: Decimal = Field(gt=0)  # seconds
    status: JobStatus = JobStatus.queued
    progress: Optional[int] = None
    error_code: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class JobCreate(BaseModel):
    """Request model for creating a new job"""
    url: HttpUrl
    start: Union[str, float, int] = Field(..., description="Start time in hh:mm:ss format or seconds")
    end: Union[str, float, int] = Field(..., description="End time in hh:mm:ss format or seconds")
    accepted_terms: bool = Field(..., description="User agreement to Terms of Use")
    
    @validator("start", "end", pre=True)
    def _to_seconds(cls, v):
        """Convert start/end to seconds - accepts hh:mm:ss strings or numeric seconds"""
        # already numeric → ok
        if isinstance(v, (int, float)):
            return float(v)
        # else parse "hh:mm:ss(.mmm)"
        parts = str(v).split(":")
        if len(parts) != 3:
            raise ValueError("Time must be in hh:mm:ss format or numeric seconds")
        try:
            h, m, s = map(float, parts)
            return h * 3600 + m * 60 + s
        except ValueError:
            raise ValueError("Invalid time format - use hh:mm:ss or numeric seconds")
    
    @validator("end")
    def validate_clip_duration(cls, end_seconds, values):
        """Validate that clip duration doesn't exceed maximum allowed"""
        start_seconds = values.get("start", 0)
        
        # Check that end > start
        if end_seconds <= start_seconds:
            raise ValueError("end time must be greater than start time")
        
        # Check maximum clip duration using environment variable
        MAX_CLIP_SECONDS = int(os.getenv("MAX_CLIP_SECONDS", "1800"))  # 30 minutes default
        duration = end_seconds - start_seconds
        
        if duration > MAX_CLIP_SECONDS:
            raise ValueError("Clip too long")
        
        return end_seconds
    
    @property 
    def start_seconds(self) -> float:
        """Get start time in seconds"""
        return self.start
    
    @property
    def end_seconds(self) -> float:
        """Get end time in seconds"""
        return self.end


class JobResponse(BaseModel):
    """Response model for job operations"""
    job_id: str
    status: JobStatus
    created_at: datetime
    progress: Optional[int] = None
    link: Optional[str] = None  # presigned S3 URL when done
    error_code: Optional[str] = None


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