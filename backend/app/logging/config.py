"""
Structured logging configuration with JSON formatting and correlation IDs.
Provides centralized logging setup for the application.
"""
import logging
import logging.config
import sys
import uuid
from contextvars import ContextVar
from typing import Any, Dict, Optional

from ..config.configuration import get_logging_settings
from ..constants import LoggingConfig

# Context variable for correlation IDs
correlation_id_context: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)


class CorrelationIdFilter(logging.Filter):
    """Filter to add correlation ID to log records"""

    def filter(self, record: logging.LogRecord) -> bool:
        correlation_id = correlation_id_context.get()
        if correlation_id:
            record.correlation_id = correlation_id
        else:
            record.correlation_id = None
        return True


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def __init__(self):
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add correlation ID if available
        if hasattr(record, "correlation_id") and record.correlation_id:
            log_entry["correlation_id"] = record.correlation_id

        # Add job ID if available
        if hasattr(record, "job_id") and record.job_id:
            log_entry["job_id"] = record.job_id

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Convert to JSON string
        import json

        return json.dumps(log_entry, default=str, ensure_ascii=False)


class StructuredLogger:
    """Enhanced logger with structured logging capabilities"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def info(self, message: str, job_id: str = None, **kwargs):
        """Log info message with optional job ID and extra fields"""
        extra = (
            {"job_id": job_id, "extra_fields": kwargs} if kwargs else {"job_id": job_id}
        )
        self.logger.info(message, extra=extra)

    def warning(self, message: str, job_id: str = None, **kwargs):
        """Log warning message with optional job ID and extra fields"""
        extra = (
            {"job_id": job_id, "extra_fields": kwargs} if kwargs else {"job_id": job_id}
        )
        self.logger.warning(message, extra=extra)

    def error(self, message: str, job_id: str = None, exc_info=None, **kwargs):
        """Log error message with optional job ID and extra fields"""
        extra = (
            {"job_id": job_id, "extra_fields": kwargs} if kwargs else {"job_id": job_id}
        )
        self.logger.error(message, extra=extra, exc_info=exc_info)

    def debug(self, message: str, job_id: str = None, **kwargs):
        """Log debug message with optional job ID and extra fields"""
        extra = (
            {"job_id": job_id, "extra_fields": kwargs} if kwargs else {"job_id": job_id}
        )
        self.logger.debug(message, extra=extra, exc_info=exc_info)


def setup_logging() -> None:
    """
    Configure structured logging for the application
    """
    settings = get_logging_settings()

    # Base configuration
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "correlation_id": {
                "()": CorrelationIdFilter,
            }
        },
        "formatters": {
            "json": {
                "()": JsonFormatter,
            },
            "text": {
                "format": LoggingConfig.DEFAULT_LOG_FORMAT,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": settings.log_format,
                "stream": sys.stdout,
                "filters": ["correlation_id"]
                if settings.enable_correlation_ids
                else [],
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": settings.log_format,
                "level": "ERROR",
                "filters": ["correlation_id"]
                if settings.enable_correlation_ids
                else [],
            },
        },
        "loggers": {
            "": {  # Root logger
                "level": settings.log_level,
                "handlers": ["console", "error_file"],
                "propagate": False,
            },
            "uvicorn": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }

    # Create logs directory if it doesn't exist
    import os

    os.makedirs("logs", exist_ok=True)

    # Apply configuration
    logging.config.dictConfig(log_config)


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance

    Args:
        name: Logger name (usually __name__)

    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)


def set_correlation_id(correlation_id: str = None) -> str:
    """
    Set correlation ID for the current context

    Args:
        correlation_id: Correlation ID to set (generates one if None)

    Returns:
        The correlation ID that was set
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())

    correlation_id_context.set(correlation_id)
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """
    Get the current correlation ID

    Returns:
        Current correlation ID or None if not set
    """
    return correlation_id_context.get()


def clear_correlation_id():
    """Clear the current correlation ID"""
    correlation_id_context.set(None)


# Convenience function to create logger instances
def create_logger(name: str) -> StructuredLogger:
    """Create a new structured logger instance"""
    return StructuredLogger(name)
