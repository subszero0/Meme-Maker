import os
from typing import Any, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    model_config = SettingsConfigDict(env_file=".env")

    # Application
    debug: bool = False

    def __init__(self, **kwargs):
        # Auto-detect debug mode from environment indicators BEFORE super().__init__
        debug_indicators = [
            os.getenv("DEBUG", "").lower() in ["true", "1", "yes"],
            os.getenv("ENVIRONMENT", "").lower() in ["development", "dev"],
            os.getenv("ENV", "").lower() in ["development", "dev"],
            os.getenv("NODE_ENV", "").lower() in ["development", "dev"],
        ]
        if any(debug_indicators):
            kwargs["debug"] = True

        super().__init__(**kwargs)

        # Log debug mode detection for troubleshooting
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"[CONFIG] Debug mode initialized: {self.debug}")
        logger.info(
            f"[CONFIG] Environment DEBUG variable: {os.getenv('DEBUG', 'not set')}"
        )

        # Check common debug environment variables
        for var in ["DEBUG", "ENVIRONMENT", "ENV", "NODE_ENV"]:
            value = os.getenv(var)
            if value:
                logger.info(f"[CONFIG] {var}={value}")

    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0

    # Rate Limiting Configuration
    global_rate_limit_requests: int = 10  # requests per minute globally
    global_rate_limit_window: int = 60  # 1 minute
    job_rate_limit_requests: int = 3  # job creations per hour
    job_rate_limit_window: int = 3600  # 1 hour

    # New configurable rate limiting
    max_jobs_per_hour: int = int(os.getenv("MAX_JOBS_PER_HOUR", "20"))
    rate_limit: str = os.getenv("RATE_LIMIT", "on")  # "on" or "off"

    # Clip length configuration
    max_clip_seconds: int = int(
        os.getenv("MAX_CLIP_SECONDS", "1800")
    )  # 30 minutes default

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
    cors_origins: Union[str, list[str]] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def validate_cors_origins(cls, v: Any) -> Union[str, list[str]]:
        """Parse CORS origins from environment variable or list"""
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        # Ensure we return the correct type
        if isinstance(v, list):
            return v
        # Fallback to string representation
        return str(v)


settings = Settings()
