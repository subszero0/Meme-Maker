"""Prometheus metrics for Meme Maker backend"""

# Import all metrics from the dedicated definitions module
from .metrics_definitions import (
    METRICS_AVAILABLE,
    clip_job_latency_seconds,
    clip_jobs_inflight, 
    clip_jobs_queued_total,
    QUEUE_DEPTH,
    JOB_DURATION,
    JOB_FAIL,
    RATE_DENIED
)

# Re-export everything for backward compatibility
__all__ = [
    "METRICS_AVAILABLE",
    "clip_job_latency_seconds",
    "clip_jobs_inflight",
    "clip_jobs_queued_total", 
    "QUEUE_DEPTH",
    "JOB_DURATION",
    "JOB_FAIL",
    "RATE_DENIED"
] 