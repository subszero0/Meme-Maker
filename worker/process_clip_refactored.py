"""
Refactored Process Clip Function

Uses the new modular architecture with proper separation of concerns.
This is the refactored version that will eventually replace the monolithic process_clip.py.
"""

import asyncio
import logging
import os
from typing import Optional

from video.processor import VideoProcessor, ProcessingRequest
from exceptions import VideoProcessingError

logger = logging.getLogger(__name__)


def should_use_refactored_processor() -> bool:
    """Check if we should use the refactored processor based on feature flag"""
    return os.getenv("USE_REFACTORED_PROCESSOR", "false").lower() == "true"


def process_clip_refactored(
    job_id: str, url: str, in_ts: float, out_ts: float, format_id: Optional[str] = None
) -> None:
    """
    Refactored video clipping job processor using modular architecture

    Args:
        job_id: Unique job identifier
        url: Video URL to process
        in_ts: Start timestamp in seconds
        out_ts: End timestamp in seconds
        format_id: Optional video format ID

    Raises:
        VideoProcessingError: If processing fails
    """
    logger.info(f"🎬 Refactored processor: Starting job {job_id}")

    try:
        # Create processing request
        request = ProcessingRequest(
            job_id=job_id, url=url, in_ts=in_ts, out_ts=out_ts, format_id=format_id
        )

        # Create processor and run
        processor = VideoProcessor(job_id)

        # Run async processing in sync context (for RQ compatibility)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(processor.process(request))

            if not result.success:
                raise VideoProcessingError(
                    result.error_message or "Processing failed",
                    job_id=job_id,
                    details={
                        "error_code": result.error_code,
                        "processing_time": result.processing_time,
                    },
                )

            logger.info(f"🎬 Refactored processor: Job {job_id} completed successfully")
            logger.info(f"🎬 Processing time: {result.processing_time:.2f}s")

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"🎬 Refactored processor: Job {job_id} failed: {e}")
        if isinstance(e, VideoProcessingError):
            raise
        else:
            raise VideoProcessingError(f"Unexpected error: {e}", job_id=job_id)


def process_clip(
    job_id: str, url: str, in_ts: float, out_ts: float, format_id: Optional[str] = None
) -> None:
    """
    Main entry point for video processing with feature flag support

    This function will route to either the legacy or refactored processor
    based on the USE_REFACTORED_PROCESSOR environment variable.

    Args:
        job_id: Unique job identifier
        url: Video URL to process
        in_ts: Start timestamp in seconds
        out_ts: End timestamp in seconds
        format_id: Optional video format ID
    """
    if should_use_refactored_processor():
        logger.info(f"🎬 Using refactored processor for job {job_id}")
        process_clip_refactored(job_id, url, in_ts, out_ts, format_id)
    else:
        # Import and use legacy processor
        from process_clip import process_clip as legacy_process_clip

        logger.info(f"🎬 Using legacy processor for job {job_id}")
        legacy_process_clip(job_id, url, in_ts, out_ts, format_id)
