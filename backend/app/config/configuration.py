"""
Centralized configuration management with validation.
All configuration parameters are defined here with proper validation.
"""
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Correctly locate the .env file at the project root
# The configuration.py file is at backend/app/config/configuration.py
# So we go up three levels to find the project root.
env_path = Path(__file__).parent.parent.parent.parent / ".env"

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"✅ Loaded environment variables from: {env_path}")
else:
    print(f"⚠️ .env file not found at {env_path}, using default settings.")


class Settings(BaseSettings):
    """Application settings"""

    # Environment settings
    debug: bool = Field(False, env="DEBUG")
    testing: bool = Field(False, env="TESTING")
    base_url: str = Field("http://localhost:8000", env="BASE_URL")

    # CORS settings
    cors_origins: list[str] = Field(default_factory=list, env="CORS_ORIGINS")

    # Redis settings
    redis_url: str = Field("redis://localhost:6379", env="REDIS_URL")

    # Storage settings
    storage_backend: str = Field("local", env="STORAGE_BACKEND")
    clips_dir: str = Field("storage/clips", env="CLIPS_DIR")
    s3_bucket_name: str = Field("", env="S3_BUCKET_NAME")
    s3_access_key_id: str = Field("", env="S3_ACCESS_KEY_ID")
    s3_secret_access_key: str = Field("", env="S3_SECRET_ACCESS_KEY")

    # FFmpeg settings
    ffmpeg_path: str = Field("ffmpeg", env="FFMPEG_PATH")
    ffprobe_path: str = Field("ffprobe", env="FFPROBE_PATH")

    # Rate limiting
    rate_limit_enabled: bool = Field(True, env="RATE_LIMIT_ENABLED")
    rate_limit_times: int = Field(100, env="RATE_LIMIT_TIMES")
    rate_limit_seconds: int = Field(60, env="RATE_LIMIT_SECONDS")

    # Pydantic settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Get the application settings, cached for performance"""
    return Settings()


class VideoProcessingSettings:
    """Video processing configuration with validation"""

    def __init__(self):
        # Constraints
        self.max_clip_duration: int = int(os.getenv("MAX_CLIP_DURATION", 180))
        self.max_concurrent_jobs: int = int(os.getenv("MAX_CONCURRENT_JOBS", 20))

        # Video Processing
        self.ffmpeg_path: str = os.getenv("FFMPEG_PATH", "ffmpeg")
        self.ffprobe_path: str = os.getenv("FFPROBE_PATH", "ffprobe")
        self.rotation_correction: float = float(os.getenv("ROTATION_CORRECTION", -1.0))

        # Storage
        self.storage_backend: str = os.getenv("STORAGE_BACKEND", "local")
        self.clips_dir: str = os.getenv("CLIPS_DIR", "/app/storage")
        self.cleanup_after_hours: int = int(os.getenv("CLEANUP_AFTER_HOURS", 24))

        # Redis
        self.redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_timeout: int = int(os.getenv("REDIS_TIMEOUT", 5))

        # External Services
        self.youtube_client_name: str = os.getenv(
            "YOUTUBE_CLIENT_NAME", "com.google.android.apps.youtube.creator/24.47.100"
        )
        self.request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", 30))

        # Worker Configuration
        self.worker_concurrency: int = int(os.getenv("WORKER_CONCURRENCY", 4))
        self.use_refactored_processor: bool = (
            os.getenv("USE_REFACTORED_PROCESSOR", "True").lower() == "true"
        )

        # API Configuration
        self.api_host: str = os.getenv("API_HOST", "0.0.0.0")
        self.api_port: int = int(os.getenv("API_PORT", 8000))
        self.base_url: str = os.getenv("BASE_URL", "http://localhost:8000")
        self.debug: bool = os.getenv("DEBUG", "False").lower() == "true"

        # Security - CORS Configuration
        cors_env = os.getenv(
            "CORS_ORIGINS", "http://localhost:3000,http://localhost:8080"
        )
        if cors_env == "*":
            self.cors_origins = ["*"]
        else:
            self.cors_origins = [origin.strip() for origin in cors_env.split(",")]

        # Always allow localhost development URLs
        dev_origins = [
            "http://localhost:3000",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
        ]
        for origin in dev_origins:
            if origin not in self.cors_origins and "*" not in self.cors_origins:
                self.cors_origins.append(origin)
        self.max_upload_size: int = int(os.getenv("MAX_UPLOAD_SIZE", 100 * 1024 * 1024))

        # Validate and create clips directory
        self._validate_clips_dir()

    def _validate_clips_dir(self):
        """Ensure clips directory exists"""
        path = Path(self.clips_dir)

        # In test environments, use a safe temporary directory if we can't create the specified path
        try:
            path.mkdir(parents=True, exist_ok=True)
            self.clips_dir = str(path)
        except (PermissionError, OSError) as e:
            # If we're in a test environment and can't create the directory,
            # use a temporary directory in the system temp location
            import sys
            import tempfile

            # Check if we're running tests (pytest sets sys.modules)
            if "pytest" in sys.modules or "unittest" in sys.modules:
                # Create a temporary directory for tests
                temp_dir = tempfile.mkdtemp(prefix="clips_test_")
                self.clips_dir = temp_dir
            else:
                # In production, re-raise the error
                raise e


class LoggingSettings:
    """Logging configuration settings"""

    def __init__(self):
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.log_format: str = os.getenv("LOG_FORMAT", "json")
        self.enable_correlation_ids: bool = (
            os.getenv("LOG_ENABLE_CORRELATION_IDS", "True").lower() == "true"
        )


class MetricsSettings:
    """Metrics and monitoring configuration"""

    def __init__(self):
        self.enable_metrics: bool = (
            os.getenv("METRICS_ENABLE_METRICS", "True").lower() == "true"
        )
        self.metrics_port: int = int(os.getenv("METRICS_METRICS_PORT", 8000))
        self.enable_tracing: bool = (
            os.getenv("METRICS_ENABLE_TRACING", "False").lower() == "true"
        )


@lru_cache()
def get_logging_settings() -> LoggingSettings:
    """Get cached logging settings instance"""
    return LoggingSettings()


@lru_cache()
def get_metrics_settings() -> MetricsSettings:
    """Get cached metrics settings instance"""
    return MetricsSettings()


# Convenience function to get all settings
def get_all_settings():
    """Get all configuration settings"""
    return {
        "app": get_settings(),
        "logging": get_logging_settings(),
        "metrics": get_metrics_settings(),
    }
