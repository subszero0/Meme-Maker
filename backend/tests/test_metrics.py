"""Tests for Prometheus metrics endpoint"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.metrics import clip_jobs_queued_total, clip_jobs_inflight, clip_job_latency_seconds


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_metrics_endpoint_exists(client):
    """Test that /metrics endpoint exists and returns 200"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"


def test_metrics_endpoint_contains_custom_metrics(client):
    """Test that custom metrics are included in the response"""
    response = client.get("/metrics")
    content = response.text
    
    # Check for custom metrics
    assert "clip_jobs_queued_total" in content
    assert "clip_jobs_inflight" in content
    assert "clip_job_latency_seconds" in content
    
    # Check for metric help text
    assert "Jobs accepted via POST /jobs" in content
    assert "Number of jobs currently working" in content
    assert "End-to-end processing time per job" in content


def test_metrics_endpoint_contains_default_metrics(client):
    """Test that default FastAPI metrics are included"""
    response = client.get("/metrics")
    content = response.text
    
    # Check for some default metrics from prometheus-fastapi-instrumentator
    assert "http_requests_total" in content
    assert "http_request_duration_seconds" in content


def test_custom_metrics_can_be_incremented():
    """Test that custom metrics can be manipulated"""
    # Get initial values
    initial_queued = clip_jobs_queued_total._value._value
    initial_inflight = clip_jobs_inflight._value._value
    
    # Increment metrics
    clip_jobs_queued_total.inc()
    clip_jobs_inflight.inc()
    
    # Verify increments
    assert clip_jobs_queued_total._value._value == initial_queued + 1
    assert clip_jobs_inflight._value._value == initial_inflight + 1
    
    # Test histogram observation
    clip_job_latency_seconds.labels(status="done").observe(1.5)
    
    # Decrement gauge
    clip_jobs_inflight.dec()
    assert clip_jobs_inflight._value._value == initial_inflight


def test_metrics_endpoint_without_auth(client):
    """Test that metrics endpoint doesn't require authentication"""
    # This test ensures the metrics endpoint is accessible without any auth headers
    response = client.get("/metrics")
    assert response.status_code == 200
    
    # Verify it's not behind any auth middleware by checking we don't get 401/403
    assert response.status_code != 401
    assert response.status_code != 403 