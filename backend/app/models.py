from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, validator


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
    in_ts: Optional[Decimal] = Field(
        default=None, ge=0
    )  # seconds (backward compatibility) - allow 0 for start of video
    out_ts: Optional[Decimal] = Field(
        default=None, gt=0
    )  # seconds (backward compatibility)
    start_time: Optional[float] = Field(default=None, ge=0)  # seconds (new field)
    end_time: Optional[float] = Field(default=None, gt=0)  # seconds (new field)
    status: JobStatus = JobStatus.queued  # Legacy field
    state: Optional[str] = None  # New state field
    progress: Optional[int] = None
    error_code: Optional[str] = None  # Legacy field
    error: Optional[str] = None  # New error field
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    download_url: Optional[str] = None  # Download URL when done - no validation needed
    stage: Optional[str] = None  # Current processing stage description
    format_id: Optional[str] = None  # Selected video format/resolution
    video_title: Optional[str] = None  # Video title for filename
    result: Optional[dict] = None  # Processing result

    @validator("download_url", "stage", "video_title", pre=True)
    def validate_optional_fields(cls, v):
        # Allow any string for download URLs, stages, and video titles (including localhost, minio, etc.)
        if v == "None":
            return None
        return v

    def to_dict(self) -> dict:
        """Convert Job to dictionary for serialization"""
        data = self.dict()
        # Convert HttpUrl to string for JSON serialization
        if isinstance(data.get("url"), HttpUrl):
            data["url"] = str(data["url"])
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Job":
        """Create Job from dictionary"""
        return cls(**data)


class JobCreate(BaseModel):
    """Request model for creating a new job"""

    url: HttpUrl
    in_ts: float = Field(ge=0)  # seconds - allow 0 for start of video
    out_ts: float = Field(gt=0)  # seconds - must be greater than 0
    format_id: Optional[str] = None  # Selected video format/resolution

    @validator("out_ts")
    def validate_out_ts(cls, v, values):
        in_ts = values.get("in_ts", 0)
        if v <= in_ts:
            raise ValueError("out_ts must be greater than in_ts")
        return v


# Additional models for the service layer
class JobCreateRequest(BaseModel):
    """Enhanced request model for job creation with validation"""

    url: HttpUrl
    start_time: float = Field(ge=0, description="Start time in seconds")
    end_time: float = Field(gt=0, description="End time in seconds")
    format_id: Optional[str] = None

    @validator("end_time")
    def validate_end_time(cls, v, values):
        start_time = values.get("start_time", 0)
        if v <= start_time:
            raise ValueError("end_time must be greater than start_time")
        return v


class JobStateUpdate(BaseModel):
    """Model for updating job state and progress"""

    state: str
    progress: int = Field(ge=0, le=100)
    stage: Optional[str] = None
    error: Optional[str] = None


class JobResponse(BaseModel):
    """Response model for job operations"""

    id: str
    status: JobStatus
    created_at: datetime
    progress: Optional[int] = None
    download_url: Optional[str] = None  # download URL when done
    error_code: Optional[str] = None
    stage: Optional[str] = None  # Current processing stage description
    format_id: Optional[str] = None  # Selected video format/resolution
    video_title: Optional[str] = None  # Video title for filename


class MetadataRequest(BaseModel):
    """Request model for fetching video metadata"""

    url: str

    @validator("url")
    def validate_url_format(cls, v):
        """Ensure the URL is a valid http/https URL format"""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        if "." not in v:
            raise ValueError("URL appears to be invalid")
        return v


class MetadataResponse(BaseModel):
    """Response model for video metadata"""

    title: str
    duration: float  # seconds
    thumbnail_url: Optional[str] = None
    resolutions: list[str] = []


class HealthResponse(BaseModel):
    """Response model for health check"""

    status: str
