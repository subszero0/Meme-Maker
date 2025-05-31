"""Prometheus metrics definitions for Meme Maker backend"""

try:
    from prometheus_client import Histogram, Gauge, Counter
    METRICS_AVAILABLE = True
    
    # Custom metrics for clip jobs
    clip_job_latency_seconds = Histogram(
        name="clip_job_latency_seconds",
        documentation="End-to-end processing time per job",
        labelnames=["status"],
        buckets=[0.5, 1, 2.5, 5, 10, 30]  # seconds
    )

    clip_jobs_inflight = Gauge(
        name="clip_jobs_inflight",
        documentation="Number of jobs currently working"
    )

    clip_jobs_queued_total = Counter(
        name="clip_jobs_queued_total",
        documentation="Jobs accepted via POST /jobs"
    )

    # New required metrics
    QUEUE_DEPTH = Gauge(
        "rq_queue_depth", 
        "Jobs waiting in RQ 'clips' queue"
    )
    
    JOB_DURATION = Histogram(
        "clip_job_duration_seconds",
        "End-to-end job processing time",
        buckets=(5, 15, 30, 60, 180, 600),
    )
    
    JOB_FAIL = Counter(
        "clip_job_fail_total",
        "Jobs that ended in error",
        ["reason"],
    )

    # Rate limiting metric
    RATE_DENIED = Counter(
        "rate_limit_denied_total",
        "Jobs blocked by rate limit"
    )

except ImportError:
    METRICS_AVAILABLE = False
    print("Warning: prometheus_client not available, metrics disabled")
    
    # Create dummy metrics that do nothing
    class DummyMetric:
        def inc(self, *args, **kwargs):
            pass
        def observe(self, *args, **kwargs):
            pass
        def set(self, *args, **kwargs):
            pass
        def time(self):
            # Return a context manager that does nothing
            from contextlib import nullcontext
            return nullcontext()
        def labels(self, *args, **kwargs):
            return self
    
    clip_job_latency_seconds = DummyMetric()
    clip_jobs_inflight = DummyMetric()
    clip_jobs_queued_total = DummyMetric()
    
    # New dummy metrics
    QUEUE_DEPTH = DummyMetric()
    JOB_DURATION = DummyMetric()
    JOB_FAIL = DummyMetric()
    RATE_DENIED = DummyMetric() 