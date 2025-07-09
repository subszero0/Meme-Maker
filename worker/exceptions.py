"""
Video Processing Exception Hierarchy

Provides structured exception handling for video processing operations
with proper error context and job correlation.
"""

from typing import Optional, Dict, Any


class VideoProcessingError(Exception):
    """Base exception for video processing operations"""

    def __init__(
        self,
        message: str,
        job_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.job_id = job_id
        self.details = details or {}
        self.error_code = self.__class__.__name__.replace("Error", "").upper()


class DownloadError(VideoProcessingError):
    """Raised when video download fails"""

    pass


class TrimError(VideoProcessingError):
    """Raised when video trimming fails"""

    pass


class StorageError(VideoProcessingError):
    """Raised when storage operations fail"""

    pass


class H264DimensionError(TrimError):
    """Raised when H.264 dimension requirements aren't met"""

    pass


class ValidationError(VideoProcessingError):
    """Raised when input validation fails"""

    pass


class QueueFullError(VideoProcessingError):
    """Raised when job queue is at capacity"""

    pass


class RepositoryError(VideoProcessingError):
    """Raised when repository operations fail"""

    pass


class FormatNotAvailableError(DownloadError):
    """Raised when requested video format is not available"""

    pass


class VideoAnalysisError(VideoProcessingError):
    """Raised when video analysis/metadata extraction fails"""

    pass


class FFmpegError(TrimError):
    """Raised when FFmpeg processing fails"""

    pass
