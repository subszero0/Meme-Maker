"""Metrics package for Meme Maker backend"""

# Import all metrics from metrics_definitions FIRST to avoid circular imports
from ..metrics_definitions import (
    METRICS_AVAILABLE,
    clip_job_latency_seconds,
    clip_jobs_inflight,
    clip_jobs_queued_total,
    QUEUE_DEPTH,
    JOB_DURATION,
    JOB_FAIL,
    RATE_DENIED
)

# Then import the updater function
from .rq_updater import start_queue_metrics_updater

# Re-export all metric names plus the updater function
__all__ = [
    "METRICS_AVAILABLE",
    "clip_job_latency_seconds",
    "clip_jobs_inflight", 
    "clip_jobs_queued_total",
    "QUEUE_DEPTH",
    "JOB_DURATION", 
    "JOB_FAIL",
    "RATE_DENIED",
    "start_queue_metrics_updater"
] 