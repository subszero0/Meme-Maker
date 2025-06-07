"""Prometheus metrics definitions for Meme Maker backend"""

from typing import Any, ContextManager, Union
from contextlib import nullcontext

# Create dummy metrics that do nothing
class DummyMetric:
    def inc(self, *args: Any, **kwargs: Any) -> None:
        pass

    def observe(self, *args: Any, **kwargs: Any) -> None:
        pass

    def set(self, *args: Any, **kwargs: Any) -> None:
        pass

    def time(self) -> ContextManager[None]:
        # Return a context manager that does nothing
        return nullcontext()

    def labels(self, *args: Any, **kwargs: Any) -> "DummyMetric":
        return self

try:
    from prometheus_client import Counter, Gauge, Histogram

    METRICS_AVAILABLE = True

    # Custom metrics for clip jobs
    clip_job_latency_seconds: Union[Histogram, DummyMetric] = Histogram(
        name="clip_job_latency_seconds",
        documentation="End-to-end processing time per job",
        labelnames=["status"],
        buckets=[0.5, 1, 2.5, 5, 10, 30],  # seconds
    )

    clip_jobs_inflight: Union[Gauge, DummyMetric] = Gauge(
        name="clip_jobs_inflight", documentation="Number of jobs currently working"
    )

    clip_jobs_queued_total: Union[Counter, DummyMetric] = Counter(
        name="clip_jobs_queued_total", documentation="Jobs accepted via POST /jobs"
    )

    # New required metrics
    QUEUE_DEPTH: Union[Gauge, DummyMetric] = Gauge("rq_queue_depth", "Jobs waiting in RQ 'clips' queue")

    JOB_DURATION: Union[Histogram, DummyMetric] = Histogram(
        "clip_job_duration_seconds",
        "End-to-end job processing time",
        buckets=(5, 15, 30, 60, 180, 600),
    )

    JOB_FAIL: Union[Counter, DummyMetric] = Counter(
        "clip_job_fail_total",
        "Jobs that ended in error",
        ["reason"],
    )

    # Rate limiting metric
    RATE_DENIED: Union[Counter, DummyMetric] = Counter("rate_limit_denied_total", "Jobs blocked by rate limit")

except ImportError:
    METRICS_AVAILABLE = False
    print("Warning: prometheus_client not available, metrics disabled")

    # Use dummy metrics when prometheus is not available
    clip_job_latency_seconds = DummyMetric()
    clip_jobs_inflight = DummyMetric()
    clip_jobs_queued_total = DummyMetric()
    QUEUE_DEPTH = DummyMetric()
    JOB_DURATION = DummyMetric()
    JOB_FAIL = DummyMetric()
    RATE_DENIED = DummyMetric()
