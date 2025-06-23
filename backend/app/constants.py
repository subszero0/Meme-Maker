"""
Application constants to eliminate magic numbers and strings.
Centralized location for all constant values used throughout the application.
"""


class VideoConstraints:
    """Video processing constraints and limits"""

    MAX_CLIP_DURATION = 180  # 3 minutes in seconds
    MIN_CLIP_DURATION = 1  # 1 second minimum
    MAX_CONCURRENT_JOBS = 20
    DEFAULT_ROTATION_CORRECTION = -1.0  # degrees
    MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
    MIN_FILE_SIZE = 1024  # 1KB


class HTTPStatusCodes:
    """HTTP status codes used in the application"""

    QUEUE_FULL = 503
    JOB_NOT_FOUND = 404
    PROCESSING_ERROR = 422
    INVALID_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    INTERNAL_ERROR = 500
    SUCCESS = 200
    CREATED = 201
    ACCEPTED = 202


class RedisKeys:
    """Redis key patterns and TTL values"""

    JOB_PREFIX = "job:"
    QUEUE_DEFAULT = "rq:queue:default"
    METADATA_PREFIX = "metadata:"
    PROGRESS_PREFIX = "progress:"

    # TTL values in seconds
    JOB_TTL = 3600  # 1 hour
    METADATA_TTL = 7200  # 2 hours
    PROGRESS_TTL = 1800  # 30 minutes


class FFmpegParams:
    """FFmpeg-related constants"""

    H264_PRESET = "fast"
    ROTATION_FILL_COLOR = "black"
    DEFAULT_FORMAT = "mp4"
    KEYFRAME_INTERVAL = 2  # seconds
    DEFAULT_CRF = 23  # quality setting
    MAX_BITRATE = "5M"

    # Audio settings
    AUDIO_CODEC = "aac"
    AUDIO_BITRATE = "128k"
    AUDIO_SAMPLE_RATE = 44100


class ErrorMessages:
    """User-facing error messages"""

    QUEUE_FULL = "Server is busy. Please try again in a moment."
    JOB_NOT_FOUND = "Job not found or has expired."
    INVALID_URL = "Invalid or unsupported URL provided."
    CLIP_TOO_LONG = "Clip duration exceeds maximum allowed length of 3 minutes."
    CLIP_TOO_SHORT = "Clip duration must be at least 1 second."
    PROCESSING_FAILED = "Video processing failed. Please try again."
    DOWNLOAD_FAILED = "Failed to download video. Please check the URL."
    STORAGE_FAILED = "Failed to save processed video."
    INVALID_TIME_RANGE = "Invalid time range specified."
    FORMAT_NOT_AVAILABLE = "Requested video format is not available."

    # Generic messages
    INTERNAL_ERROR = "An internal error occurred. Please try again later."
    VALIDATION_ERROR = "Invalid input data provided."
    UNAUTHORIZED_ACCESS = "Unauthorized access."


class JobStates:
    """Job processing states"""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VideoFormats:
    """Supported video formats and codecs"""

    SUPPORTED_CONTAINERS = ["mp4", "webm", "mkv", "avi", "mov"]
    SUPPORTED_VIDEO_CODECS = ["h264", "vp9", "vp8", "av1"]
    SUPPORTED_AUDIO_CODECS = ["aac", "opus", "mp3", "vorbis"]

    DEFAULT_CONTAINER = "mp4"
    DEFAULT_VIDEO_CODEC = "h264"
    DEFAULT_AUDIO_CODEC = "aac"


class StorageConfig:
    """Storage-related constants"""

    LOCAL_STORAGE_DIR = "/app/storage"
    TEMP_DIR = "/tmp/video_processing"
    UPLOAD_CHUNK_SIZE = 8192  # 8KB
    MAX_FILENAME_LENGTH = 255

    # File organization
    DATE_FORMAT = "%Y/%m/%d"
    FILENAME_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"


class RateLimits:
    """Rate limiting configuration"""

    # Global limits (per IP)
    REQUESTS_PER_MINUTE = 60
    REQUESTS_PER_HOUR = 1000

    # Endpoint-specific limits
    JOBS_PER_HOUR = 50
    METADATA_REQUESTS_PER_MINUTE = 30

    # Rate limit windows
    MINUTE_WINDOW = 60  # seconds
    HOUR_WINDOW = 3600  # seconds


class MetricsConfig:
    """Metrics and monitoring constants"""

    METRICS_NAMESPACE = "video_processor"
    HISTOGRAM_BUCKETS = [0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]

    # Metric names
    JOB_DURATION_METRIC = "job_processing_duration_seconds"
    JOB_TOTAL_METRIC = "jobs_total"
    QUEUE_SIZE_METRIC = "queue_size"
    ERROR_RATE_METRIC = "error_rate"


class LoggingConfig:
    """Logging configuration constants"""

    DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    JSON_LOG_FORMAT = "json"

    # Log levels
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    # Correlation ID header
    CORRELATION_ID_HEADER = "X-Correlation-ID"


class APIConfig:
    """API-related constants"""

    API_VERSION = "v1"
    API_PREFIX = f"/api/{API_VERSION}"

    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100

    # Request timeouts
    DEFAULT_TIMEOUT = 30
    LONG_TIMEOUT = 300  # 5 minutes for processing


class SecurityConfig:
    """Security-related constants"""

    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
    CORS_MAX_AGE = 3600

    # Content types
    ALLOWED_CONTENT_TYPES = [
        "application/json",
        "multipart/form-data",
        "application/x-www-form-urlencoded",
    ]


class WorkerConfig:
    """Worker process configuration"""

    DEFAULT_CONCURRENCY = 4
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds

    # Queue names
    DEFAULT_QUEUE = "default"
    HIGH_PRIORITY_QUEUE = "high"
    LOW_PRIORITY_QUEUE = "low"


class AsyncConfig:
    """AsyncIO configuration constants"""

    MAX_CONCURRENT_JOBS = 5
    BATCH_SIZE = 10
    PROCESSING_TIMEOUT = 300  # 5 minutes
    EXECUTOR_WORKERS = 4

    # Connection pooling
    MAX_CONNECTIONS = 100
    CONNECTION_TIMEOUT = 30

    # Background tasks
    CLEANUP_INTERVAL_HOURS = 6
    CACHE_CLEANUP_INTERVAL_HOURS = 12


class CacheConfig:
    """Cache configuration constants"""

    DEFAULT_TTL = 3600  # 1 hour
    METADATA_TTL = 3600  # 1 hour for metadata
    FORMAT_TTL = 7200  # 2 hours for format detection
    THUMBNAIL_TTL = 86400  # 24 hours for thumbnails

    # Cache key prefixes
    METADATA_PREFIX = "cache:metadata:"
    FORMAT_PREFIX = "cache:format:"
    THUMBNAIL_PREFIX = "cache:thumbnail:"
