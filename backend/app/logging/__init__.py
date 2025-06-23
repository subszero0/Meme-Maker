"""
Structured logging package.
Provides centralized logging configuration with JSON formatting and correlation IDs.
"""

from .config import (
    StructuredLogger,
    clear_correlation_id,
    create_logger,
    get_correlation_id,
    get_logger,
    set_correlation_id,
    setup_logging,
)

__all__ = [
    "setup_logging",
    "get_logger",
    "set_correlation_id",
    "get_correlation_id",
    "clear_correlation_id",
    "create_logger",
    "StructuredLogger",
]
