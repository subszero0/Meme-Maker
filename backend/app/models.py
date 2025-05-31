from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, HttpUrl, Field
from decimal import Decimal
from dataclasses import dataclass


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
    start: str = Field(..., description="Start time in ISO format (hh:mm:ss)")
    end: str = Field(..., description="End time in ISO format (hh:mm:ss)")
    accepted_terms: bool = Field(..., description="User agreement to Terms of Use")
    
    def to_seconds(self, time_str: str) -> float:
        """Convert hh:mm:ss string to seconds"""
        parts = time_str.split(':')
        if len(parts) != 3:
            raise ValueError("Time must be in format hh:mm:ss")
        
        hours, minutes, seconds = map(float, parts)
        return hours * 3600 + minutes * 60 + seconds
    
    @property 
    def start_seconds(self) -> float:
        """Get start time in seconds"""
        return self.to_seconds(self.start)
    
    @property
    def end_seconds(self) -> float:
        """Get end time in seconds"""
        return self.to_seconds(self.end)


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