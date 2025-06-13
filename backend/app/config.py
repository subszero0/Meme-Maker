from pydantic import BaseSettings, validator
from typing import Optional, Union


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    debug: bool = False
    
    # Redis Configuration
    redis_url: str = "redis://redis:6379"  # Default to docker service name
    redis_db: int = 0
    
    # AWS S3 Configuration
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "ap-south-1"
    aws_endpoint_url: Optional[str] = None  # For MinIO compatibility
    s3_bucket: str = "clip-files-dev"
    
    # Worker Configuration
    max_concurrent_jobs: int = 20
    job_timeout: int = 300  # 5 minutes
    yt_dlp_path: str = "/usr/local/bin/yt-dlp"
    ffmpeg_path: str = "/usr/local/bin/ffmpeg"
    
    # Security
    cors_origins: Union[str, list[str]] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:8000", "https://clip.yourdomain.com"]
    
    @validator("cors_origins", pre=True)
    def validate_cors_origins(cls, v):
        """Parse CORS origins from environment variable or list"""
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    class Config:
        env_file = ".env"


settings = Settings() 