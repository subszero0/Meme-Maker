"""
Centralized configuration management with validation.
All configuration parameters are defined here with proper validation.
"""
import os
from functools import lru_cache
from pathlib import Path


class VideoProcessingSettings:
    """Video processing configuration with validation"""

    def __init__(self):
        # Constraints
        self.max_clip_duration: int = int(os.getenv("MAX_CLIP_DURATION", 180))
        self.max_concurrent_jobs: int = int(os.getenv("MAX_CONCURRENT_JOBS", 20))

        # Video Processing
        self.ffmpeg_path: str = os.getenv("FFMPEG_PATH", "/usr/bin/ffmpeg")
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
        path.mkdir(parents=True, exist_ok=True)
        self.clips_dir = str(path)


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
def get_settings() -> VideoProcessingSettings:
    """Get cached settings instance"""
    return VideoProcessingSettings()


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
