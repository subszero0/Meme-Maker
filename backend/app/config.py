from pydantic_settings import BaseSettings
from pydantic import validator
from typing import Optional, Union


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    debug: bool = False
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    
    # Rate Limiting Configuration
    global_rate_limit_requests: int = 10  # requests per minute globally
    global_rate_limit_window: int = 60  # 1 minute
    job_rate_limit_requests: int = 3  # job creations per hour
    job_rate_limit_window: int = 3600  # 1 hour
    
    # MinIO/S3 Configuration  
    aws_access_key_id: str = "admin"
    aws_secret_access_key: str = "admin12345"
    aws_region: str = "ap-south-1" 
    aws_endpoint_url: str = "http://minio:9000"  # MinIO endpoint within Docker network
    s3_bucket: str = "clips"
    
    # Worker Configuration
    max_concurrent_jobs: int = 20
    job_timeout: int = 300  # 5 minutes
    yt_dlp_path: str = "/usr/local/bin/yt-dlp"
    ffmpeg_path: str = "/usr/local/bin/ffmpeg"
    
    # Security
    cors_origins: Union[str, list[str]] = ["http://localhost:3000", "http://localhost:8000"]
    
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