"""
Unit tests for exception hierarchy
"""

import pytest
from exceptions import (
    VideoProcessingError,
    DownloadError,
    TrimError,
    StorageError,
    H264DimensionError,
    ValidationError,
    QueueFullError,
    RepositoryError,
    FormatNotAvailableError,
    VideoAnalysisError,
    FFmpegError,
)


class TestVideoProcessingError:
    """Test base exception class"""

    def test_creation_with_message_only(self):
        """Test creating exception with message only"""
        error = VideoProcessingError("Test error")
        assert str(error) == "Test error"
        assert error.job_id is None
        assert error.details == {}
        assert error.error_code == "VIDEOPROCESSING"

    def test_creation_with_job_id(self):
        """Test creating exception with job ID"""
        error = VideoProcessingError("Test error", job_id="job123")
        assert str(error) == "Test error"
        assert error.job_id == "job123"
        assert error.details == {}

    def test_creation_with_details(self):
        """Test creating exception with details"""
        details = {"url": "test.com", "format": "mp4"}
        error = VideoProcessingError("Test error", details=details)
        assert str(error) == "Test error"
        assert error.details == details

    def test_creation_with_all_params(self):
        """Test creating exception with all parameters"""
        details = {"url": "test.com"}
        error = VideoProcessingError("Test error", job_id="job123", details=details)
        assert str(error) == "Test error"
        assert error.job_id == "job123"
        assert error.details == details


class TestDownloadError:
    """Test download-specific exception"""

    def test_inheritance(self):
        """Test that DownloadError inherits from VideoProcessingError"""
        error = DownloadError("Download failed")
        assert isinstance(error, VideoProcessingError)
        assert error.error_code == "DOWNLOAD"

    def test_format_not_available_inheritance(self):
        """Test that FormatNotAvailableError inherits from DownloadError"""
        error = FormatNotAvailableError("Format not available")
        assert isinstance(error, DownloadError)
        assert isinstance(error, VideoProcessingError)
        assert error.error_code == "FORMATNOTAVAILABLE"


class TestTrimError:
    """Test trim-specific exceptions"""

    def test_inheritance(self):
        """Test that TrimError inherits from VideoProcessingError"""
        error = TrimError("Trim failed")
        assert isinstance(error, VideoProcessingError)
        assert error.error_code == "TRIM"

    def test_h264_dimension_error_inheritance(self):
        """Test that H264DimensionError inherits from TrimError"""
        error = H264DimensionError("Dimension error")
        assert isinstance(error, TrimError)
        assert isinstance(error, VideoProcessingError)
        assert error.error_code == "H264DIMENSION"

    def test_ffmpeg_error_inheritance(self):
        """Test that FFmpegError inherits from TrimError"""
        error = FFmpegError("FFmpeg failed")
        assert isinstance(error, TrimError)
        assert isinstance(error, VideoProcessingError)
        assert error.error_code == "FFMPEG"


class TestStorageError:
    """Test storage-specific exception"""

    def test_inheritance(self):
        """Test that StorageError inherits from VideoProcessingError"""
        error = StorageError("Storage failed")
        assert isinstance(error, VideoProcessingError)
        assert error.error_code == "STORAGE"


class TestValidationError:
    """Test validation-specific exception"""

    def test_inheritance(self):
        """Test that ValidationError inherits from VideoProcessingError"""
        error = ValidationError("Validation failed")
        assert isinstance(error, VideoProcessingError)
        assert error.error_code == "VALIDATION"


class TestQueueFullError:
    """Test queue-specific exception"""

    def test_inheritance(self):
        """Test that QueueFullError inherits from VideoProcessingError"""
        error = QueueFullError("Queue full")
        assert isinstance(error, VideoProcessingError)
        assert error.error_code == "QUEUEFULL"


class TestRepositoryError:
    """Test repository-specific exception"""

    def test_inheritance(self):
        """Test that RepositoryError inherits from VideoProcessingError"""
        error = RepositoryError("Repository failed")
        assert isinstance(error, VideoProcessingError)
        assert error.error_code == "REPOSITORY"


class TestVideoAnalysisError:
    """Test video analysis-specific exception"""

    def test_inheritance(self):
        """Test that VideoAnalysisError inherits from VideoProcessingError"""
        error = VideoAnalysisError("Analysis failed")
        assert isinstance(error, VideoProcessingError)
        assert error.error_code == "VIDEOANALYSIS"


class TestErrorCodeGeneration:
    """Test automatic error code generation"""

    def test_error_codes_are_correct(self):
        """Test that error codes are generated correctly from class names"""
        test_cases = [
            (VideoProcessingError, "VIDEOPROCESSING"),
            (DownloadError, "DOWNLOAD"),
            (TrimError, "TRIM"),
            (StorageError, "STORAGE"),
            (H264DimensionError, "H264DIMENSION"),
            (ValidationError, "VALIDATION"),
            (QueueFullError, "QUEUEFULL"),
            (RepositoryError, "REPOSITORY"),
            (FormatNotAvailableError, "FORMATNOTAVAILABLE"),
            (VideoAnalysisError, "VIDEOANALYSIS"),
            (FFmpegError, "FFMPEG"),
        ]

        for error_class, expected_code in test_cases:
            error = error_class("Test message")
            assert error.error_code == expected_code
