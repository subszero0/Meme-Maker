"""Prometheus metrics for Meme Maker backend"""

try:
    from prometheus_client import Counter, Gauge, Histogram

    METRICS_AVAILABLE = True

    # Custom metrics for clip jobs
    clip_job_latency_seconds = Histogram(
        name="clip_job_latency_seconds",
        documentation="End-to-end processing time per job",
        labelnames=["status"],
        buckets=[0.5, 1, 2.5, 5, 10, 30],  # seconds
    )

    clip_jobs_inflight = Gauge(
        name="clip_jobs_inflight", documentation="Number of jobs currently working"
    )

    clip_jobs_queued_total = Counter(
        name="clip_jobs_queued_total", documentation="Jobs accepted via POST /jobs"
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

    clip_job_latency_seconds = DummyMetric()
    clip_jobs_inflight = DummyMetric()
    clip_jobs_queued_total = DummyMetric()
