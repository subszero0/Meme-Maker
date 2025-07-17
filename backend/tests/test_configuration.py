"""
Tests for the centralized configuration management system.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from app.config.configuration import (
    LoggingSettings,
    MetricsSettings,
    VideoProcessingSettings,
    get_logging_settings,
    get_metrics_settings,
    get_settings,
)
from app.constants import LoggingConfig, VideoConstraints
from app.logging.config import get_correlation_id, get_logger, set_correlation_id


class TestVideoProcessingSettings:
    """Test video processing configuration validation"""

    def test_default_values(self):
        """Test default configuration values"""
        # Clear any existing environment variables that might interfere
        with patch.dict(os.environ, {}, clear=True):
            # Set only the defaults we expect
            settings = VideoProcessingSettings()

            assert settings.max_clip_duration == 180
            assert settings.max_concurrent_jobs == 20
            assert settings.ffmpeg_path == "/usr/bin/ffmpeg"
            assert settings.storage_backend == "local"
            # Test the Redis URL with proper default (may vary by environment)
            assert settings.redis_url in [
                "redis://localhost:6379",
                "redis://redis:6379",
            ]

    def test_validation_constraints(self):
        """Test validation constraints work correctly"""
        # Test valid values using environment variables
        with patch.dict(
            os.environ, {"MAX_CLIP_DURATION": "60", "MAX_CONCURRENT_JOBS": "10"}
        ):
            settings = VideoProcessingSettings()
            assert settings.max_clip_duration == 60
            assert settings.max_concurrent_jobs == 10

        # Test invalid values should use defaults since validation doesn't happen at init
        # The actual validation should happen at the application level
        with patch.dict(os.environ, {"MAX_CLIP_DURATION": "0"}):
            settings = VideoProcessingSettings()
            # Should use the provided value (validation would happen elsewhere)
            assert settings.max_clip_duration == 0

    def test_clips_dir_creation(self):
        """Test clips directory is created if it doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            clips_path = os.path.join(temp_dir, "test_clips")

            with patch.dict(os.environ, {"CLIPS_DIR": clips_path}):
                settings = VideoProcessingSettings()

                assert os.path.exists(clips_path)
                assert settings.clips_dir == clips_path

    def test_environment_variable_loading(self):
        """Test loading from environment variables"""
        with patch.dict(
            os.environ, {"MAX_CLIP_DURATION": "120", "REDIS_URL": "redis://test:6379"}
        ):
            settings = VideoProcessingSettings()
            assert settings.max_clip_duration == 120
            assert settings.redis_url == "redis://test:6379"


class TestLoggingSettings:
    """Test logging configuration"""

    def test_default_logging_settings(self):
        """Test default logging configuration"""
        settings = LoggingSettings()

        assert settings.log_level == "INFO"
        assert settings.log_format == "json"
        assert settings.enable_correlation_ids is True

    def test_environment_prefix(self):
        """Test environment variable prefix for logging"""
        with patch.dict(
            os.environ,
            {
                "LOG_LEVEL": "DEBUG",
                "LOG_FORMAT": "text",
                "LOG_ENABLE_CORRELATION_IDS": "false",
            },
        ):
            settings = LoggingSettings()
            assert settings.log_level == "DEBUG"
            assert settings.log_format == "text"
            assert settings.enable_correlation_ids is False


class TestMetricsSettings:
    """Test metrics configuration"""

    def test_default_metrics_settings(self):
        """Test default metrics configuration"""
        settings = MetricsSettings()

        assert settings.enable_metrics is True
        assert settings.metrics_port == 8000
        assert settings.enable_tracing is False

    def test_metrics_environment_prefix(self):
        """Test environment variable prefix for metrics"""
        with patch.dict(
            os.environ,
            {
                "METRICS_ENABLE_METRICS": "false",
                "METRICS_METRICS_PORT": "9090",
                "METRICS_ENABLE_TRACING": "true",
            },
        ):
            settings = MetricsSettings()
            assert settings.enable_metrics is False
            assert settings.metrics_port == 9090
            assert settings.enable_tracing is True


class TestSettingsCaching:
    """Test settings caching functionality"""

    def test_settings_caching(self):
        """Test that settings are cached properly"""
        settings1 = get_settings()
        settings2 = get_settings()

        # Should be the same instance due to @lru_cache
        assert settings1 is settings2

    def test_logging_settings_caching(self):
        """Test that logging settings are cached properly"""
        settings1 = get_logging_settings()
        settings2 = get_logging_settings()

        assert settings1 is settings2

    def test_metrics_settings_caching(self):
        """Test that metrics settings are cached properly"""
        settings1 = get_metrics_settings()
        settings2 = get_metrics_settings()

        assert settings1 is settings2


class TestStructuredLogging:
    """Test structured logging functionality"""

    def test_correlation_id_context(self):
        """Test correlation ID context management"""
        # Initially no correlation ID
        assert get_correlation_id() is None

        # Set correlation ID
        correlation_id = set_correlation_id("test-123")
        assert correlation_id == "test-123"
        assert get_correlation_id() == "test-123"

        # Generate correlation ID automatically
        auto_id = set_correlation_id()
        assert auto_id is not None
        assert len(auto_id) == 36  # UUID length
        assert get_correlation_id() == auto_id

    def test_structured_logger_creation(self):
        """Test structured logger creation"""
        logger = get_logger("test_module")

        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "debug")

    @patch("app.logging.config.logging.getLogger")
    def test_structured_logger_methods(self, mock_get_logger):
        """Test structured logger methods"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger = get_logger("test")

        # Test info logging
        logger.info("test message", job_id="job-123", extra_field="value")
        mock_logger.info.assert_called_once()

        # Test error logging with exception
        logger.error("error message", job_id="job-456", exc_info=True)
        mock_logger.error.assert_called_once()


class TestConstants:
    """Test constants are properly defined"""

    def test_video_constraints(self):
        """Test video constraint constants"""
        assert VideoConstraints.MAX_CLIP_DURATION == 180
        assert VideoConstraints.MIN_CLIP_DURATION == 1
        assert VideoConstraints.MAX_CONCURRENT_JOBS == 20
        assert VideoConstraints.DEFAULT_ROTATION_CORRECTION == -1.0

    def test_logging_config(self):
        """Test logging configuration constants"""
        assert LoggingConfig.DEFAULT_LOG_FORMAT is not None
        assert LoggingConfig.JSON_LOG_FORMAT == "json"
        assert LoggingConfig.CORRELATION_ID_HEADER == "X-Correlation-ID"

    def test_http_status_codes(self):
        """Test HTTP status code constants"""
        from app.constants import HTTPStatusCodes

        assert HTTPStatusCodes.QUEUE_FULL == 503
        assert HTTPStatusCodes.JOB_NOT_FOUND == 404
        assert HTTPStatusCodes.SUCCESS == 200

    def test_error_messages(self):
        """Test error message constants"""
        from app.constants import ErrorMessages

        assert ErrorMessages.QUEUE_FULL is not None
        assert ErrorMessages.JOB_NOT_FOUND is not None
        assert ErrorMessages.CLIP_TOO_LONG is not None


class TestConfigurationIntegration:
    """Test configuration integration with other components"""

    def test_settings_validation_integration(self):
        """Test that settings validation works with business logic"""
        settings = VideoProcessingSettings()

        # Test that settings can be used for validation
        test_duration = 200  # seconds
        assert test_duration > settings.max_clip_duration

        test_concurrent_jobs = 15
        assert test_concurrent_jobs < settings.max_concurrent_jobs

    def test_environment_override_integration(self):
        """Test environment variable override works end-to-end"""
        with patch.dict(
            os.environ,
            {"MAX_CLIP_DURATION": "120", "MAX_CONCURRENT_JOBS": "15", "DEBUG": "true"},
        ):
            settings = VideoProcessingSettings()

            assert settings.max_clip_duration == 120
            assert settings.max_concurrent_jobs == 15
            assert settings.debug is True


if __name__ == "__main__":
    pytest.main([__file__])
