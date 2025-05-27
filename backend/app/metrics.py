"""Prometheus metrics for Meme Maker backend"""

from prometheus_client import Histogram, Gauge, Counter

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