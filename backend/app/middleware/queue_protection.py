"""
🚨 T-003 Queue DoS Protection Middleware (CVSS 8.6)
Comprehensive protection against queue draining and resource exhaustion attacks.
Implements circuit breaker, queue monitoring, and advanced rate limiting.
"""

import asyncio
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..config.configuration import get_settings
from ..constants import RateLimits
from ..logging.config import get_logger

logger = get_logger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service has recovered


@dataclass
class QueueMetrics:
    """Queue health metrics"""

    current_depth: int
    processing_jobs: int
    failed_jobs_last_hour: int
    average_processing_time: float
    error_rate: float
    timestamp: float


@dataclass
class IPBehavior:
    """IP behavior tracking for advanced DoS detection"""

    request_times: deque
    job_submissions: deque
    burst_violations: int
    last_burst_time: float
    total_jobs_today: int
    last_daily_reset: float
    concurrent_jobs: int
    penalty_until: float


class CircuitBreaker:
    """Circuit breaker for queue protection"""

    def __init__(self):
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.request_count = 0
        self.last_failure_time = 0
        self.next_attempt_time = 0

    def record_success(self):
        """Record successful request"""
        self.failure_count = 0
        self.request_count += 1
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            logger.info("Circuit breaker: Recovered, switching to CLOSED")

    def record_failure(self):
        """Record failed request"""
        self.failure_count += 1
        self.request_count += 1
        self.last_failure_time = time.time()

        # Check if we should open the circuit
        if (
            self.request_count >= RateLimits.MIN_REQUESTS_FOR_CIRCUIT
            and self.failure_count / self.request_count
            >= RateLimits.ERROR_RATE_THRESHOLD
        ):
            self.state = CircuitBreakerState.OPEN
            self.next_attempt_time = time.time() + RateLimits.CIRCUIT_BREAKER_TIMEOUT
            logger.warning(
                f"Circuit breaker: OPENED due to error rate {self.failure_count}/{self.request_count}"
            )

    def can_request(self) -> bool:
        """Check if request can proceed"""
        now = time.time()

        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if now >= self.next_attempt_time:
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info("Circuit breaker: Switching to HALF_OPEN for testing")
                return True
            return False
        elif self.state == CircuitBreakerState.HALF_OPEN:
            return True

        return False


class QueueDosProtection:
    """Advanced Queue DoS Protection System"""

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.settings = get_settings()

        # Circuit breaker
        self.circuit_breaker = CircuitBreaker()

        # IP behavior tracking
        self.ip_behaviors: Dict[str, IPBehavior] = {}

        # Queue metrics
        self.queue_metrics_history: List[QueueMetrics] = []

        # Cleanup intervals
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes

    def get_client_ip(self, request: Request) -> str:
        """Extract client IP with enhanced detection"""
        # Check various headers for real IP
        for header in ["X-Forwarded-For", "X-Real-IP", "CF-Connecting-IP"]:
            value = request.headers.get(header)
            if value:
                # Take first IP for X-Forwarded-For
                return value.split(",")[0].strip()

        return request.client.host if request.client else "unknown"

    def get_or_create_ip_behavior(self, client_ip: str) -> IPBehavior:
        """Get or create IP behavior tracking"""
        if client_ip not in self.ip_behaviors:
            now = time.time()
            self.ip_behaviors[client_ip] = IPBehavior(
                request_times=deque(maxlen=100),
                job_submissions=deque(maxlen=50),
                burst_violations=0,
                last_burst_time=0,
                total_jobs_today=0,
                last_daily_reset=now,
                concurrent_jobs=0,
                penalty_until=0,
            )

        return self.ip_behaviors[client_ip]

    async def get_queue_metrics(self) -> QueueMetrics:
        """Get current queue health metrics"""
        try:
            if not self.redis_client:
                # Fallback metrics when Redis unavailable
                return QueueMetrics(
                    current_depth=0,
                    processing_jobs=0,
                    failed_jobs_last_hour=0,
                    average_processing_time=0.0,
                    error_rate=0.0,
                    timestamp=time.time(),
                )

            # Get queue depth
            queue_depth = (
                await asyncio.to_thread(self.redis_client.llen, "rq:queue:default")
                if hasattr(self.redis_client, "llen")
                else 0
            )

            # Get processing jobs (simplified)
            processing_jobs = queue_depth  # Simplified metric

            # Calculate basic metrics
            metrics = QueueMetrics(
                current_depth=queue_depth,
                processing_jobs=processing_jobs,
                failed_jobs_last_hour=0,  # Simplified
                average_processing_time=30.0,  # Estimated
                error_rate=self.circuit_breaker.failure_count
                / max(self.circuit_breaker.request_count, 1),
                timestamp=time.time(),
            )

            # Store metrics history
            self.queue_metrics_history.append(metrics)
            if len(self.queue_metrics_history) > 100:
                self.queue_metrics_history.pop(0)

            return metrics

        except Exception as e:
            logger.error(f"Failed to get queue metrics: {e}")
            return QueueMetrics(
                current_depth=0,
                processing_jobs=0,
                failed_jobs_last_hour=0,
                average_processing_time=0.0,
                error_rate=0.0,
                timestamp=time.time(),
            )

    def check_burst_detection(
        self, ip_behavior: IPBehavior, client_ip: str
    ) -> Tuple[bool, Optional[str]]:
        """Check for burst attack patterns"""
        now = time.time()

        # Reset daily counter
        if now - ip_behavior.last_daily_reset > RateLimits.DAY_WINDOW:
            ip_behavior.total_jobs_today = 0
            ip_behavior.last_daily_reset = now

        # Check if in penalty period
        if now < ip_behavior.penalty_until:
            remaining = int(ip_behavior.penalty_until - now)
            return (
                False,
                f"IP in penalty period for {remaining} seconds due to burst detection",
            )

        # Add current request time
        ip_behavior.request_times.append(now)

        # Check burst pattern (too many requests in short time)
        recent_requests = [
            t
            for t in ip_behavior.request_times
            if now - t <= RateLimits.BURST_DETECTION_WINDOW
        ]

        if len(recent_requests) > RateLimits.MAX_BURST_REQUESTS:
            ip_behavior.burst_violations += 1
            ip_behavior.last_burst_time = now
            ip_behavior.penalty_until = now + (RateLimits.BURST_PENALTY_MINUTES * 60)

            logger.warning(
                f"Burst detected for IP {client_ip}: {len(recent_requests)} requests in {RateLimits.BURST_DETECTION_WINDOW}s"
            )
            return (
                False,
                f"Burst detected: {len(recent_requests)} requests in {RateLimits.BURST_DETECTION_WINDOW} seconds",
            )

        return True, None

    def check_job_limits(
        self, ip_behavior: IPBehavior, client_ip: str, is_job_request: bool
    ) -> Tuple[bool, Optional[str]]:
        """Check job-specific limits"""
        now = time.time()

        if not is_job_request:
            return True, None

        # Check daily job limit
        if ip_behavior.total_jobs_today >= RateLimits.JOBS_PER_DAY:
            return (
                False,
                f"Daily job limit exceeded: {ip_behavior.total_jobs_today}/{RateLimits.JOBS_PER_DAY}",
            )

        # Check hourly job limit
        recent_jobs = [
            t for t in ip_behavior.job_submissions if now - t <= RateLimits.HOUR_WINDOW
        ]

        if len(recent_jobs) >= RateLimits.JOBS_PER_HOUR:
            return (
                False,
                f"Hourly job limit exceeded: {len(recent_jobs)}/{RateLimits.JOBS_PER_HOUR}",
            )

        # Check concurrent jobs
        if ip_behavior.concurrent_jobs >= RateLimits.CONCURRENT_JOBS_PER_IP:
            return (
                False,
                f"Concurrent job limit exceeded: {ip_behavior.concurrent_jobs}/{RateLimits.CONCURRENT_JOBS_PER_IP}",
            )

        return True, None

    async def check_queue_health(self) -> Tuple[bool, Optional[str]]:
        """Check overall queue health"""
        metrics = await self.get_queue_metrics()

        # Check circuit breaker
        if not self.circuit_breaker.can_request():
            return False, f"Circuit breaker is {self.circuit_breaker.state.value}"

        # Check queue depth
        if metrics.current_depth >= RateLimits.MAX_QUEUE_DEPTH:
            return (
                False,
                f"Queue at capacity: {metrics.current_depth}/{RateLimits.MAX_QUEUE_DEPTH}",
            )

        # Check queue critical threshold
        if metrics.current_depth >= RateLimits.QUEUE_CRITICAL_THRESHOLD:
            logger.warning(
                f"Queue at critical level: {metrics.current_depth}/{RateLimits.QUEUE_CRITICAL_THRESHOLD}"
            )

        return True, None

    async def validate_request(
        self, request: Request
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Main validation function for incoming requests"""
        client_ip = self.get_client_ip(request)
        is_job_request = "/api/v1/jobs" in str(request.url)

        # Get IP behavior
        ip_behavior = self.get_or_create_ip_behavior(client_ip)

        # Check burst detection
        burst_ok, burst_msg = self.check_burst_detection(ip_behavior, client_ip)
        if not burst_ok:
            return False, {
                "error": "Rate limit exceeded",
                "message": burst_msg,
                "limit_type": "burst_protection",
                "client_ip": client_ip,
                "retry_after": RateLimits.BURST_PENALTY_MINUTES * 60,
            }

        # Check job-specific limits
        if is_job_request:
            job_ok, job_msg = self.check_job_limits(ip_behavior, client_ip, True)
            if not job_ok:
                return False, {
                    "error": "Job limit exceeded",
                    "message": job_msg,
                    "limit_type": "job_limit",
                    "client_ip": client_ip,
                    "retry_after": 3600,  # 1 hour
                }

        # Check queue health
        queue_ok, queue_msg = await self.check_queue_health()
        if not queue_ok:
            return False, {
                "error": "Service unavailable",
                "message": queue_msg,
                "limit_type": "queue_protection",
                "retry_after": 300,  # 5 minutes
            }

        # Track successful validation
        if is_job_request:
            ip_behavior.job_submissions.append(time.time())
            ip_behavior.total_jobs_today += 1
            ip_behavior.concurrent_jobs += 1

        return True, None

    def record_job_completion(self, client_ip: str, success: bool):
        """Record job completion for tracking"""
        if client_ip in self.ip_behaviors:
            self.ip_behaviors[client_ip].concurrent_jobs = max(
                0, self.ip_behaviors[client_ip].concurrent_jobs - 1
            )

        if success:
            self.circuit_breaker.record_success()
        else:
            self.circuit_breaker.record_failure()

    async def cleanup_old_data(self):
        """Clean up old tracking data"""
        now = time.time()

        if now - self.last_cleanup < self.cleanup_interval:
            return

        self.last_cleanup = now

        # Clean up old IP behaviors
        old_ips = []
        for ip, behavior in self.ip_behaviors.items():
            # Remove IPs with no recent activity (1 hour)
            if behavior.request_times and now - behavior.request_times[-1] > 3600:
                old_ips.append(ip)

        for ip in old_ips:
            del self.ip_behaviors[ip]

        logger.debug(f"Cleaned up {len(old_ips)} old IP behaviors")


class QueueDosProtectionMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for Queue DoS protection"""

    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self.protection = QueueDosProtection(redis_client)

        # Excluded paths
        self.excluded_paths = {
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        }

    async def dispatch(self, request: Request, call_next):
        """Process request through DoS protection"""
        # Skip protection for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Validate request
        is_allowed, error_info = await self.protection.validate_request(request)

        if not is_allowed and error_info:
            logger.warning(
                f"DoS protection blocked request from {error_info.get('client_ip')} "
                f"({error_info.get('limit_type')}): {error_info.get('message')}"
            )

            headers = {}
            if "retry_after" in error_info:
                headers["Retry-After"] = str(error_info["retry_after"])

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=error_info,
                headers=headers,
            )

        # Process request
        try:
            response = await call_next(request)

            # Record success for job requests
            if "/api/v1/jobs" in str(request.url) and response.status_code < 400:
                client_ip = self.protection.get_client_ip(request)
                self.protection.record_job_completion(client_ip, True)

            return response

        except Exception as e:
            # Record failure
            if "/api/v1/jobs" in str(request.url):
                client_ip = self.protection.get_client_ip(request)
                self.protection.record_job_completion(client_ip, False)

            raise e
        finally:
            # Cleanup old data periodically
            await self.protection.cleanup_old_data()


# Admin endpoint for monitoring
async def get_queue_protection_status(protection: QueueDosProtection) -> Dict[str, Any]:
    """Get current queue protection status"""
    metrics = await protection.get_queue_metrics()

    return {
        "circuit_breaker": {
            "state": protection.circuit_breaker.state.value,
            "failure_count": protection.circuit_breaker.failure_count,
            "request_count": protection.circuit_breaker.request_count,
        },
        "queue_metrics": {
            "current_depth": metrics.current_depth,
            "processing_jobs": metrics.processing_jobs,
            "error_rate": metrics.error_rate,
        },
        "protection_settings": {
            "max_queue_depth": RateLimits.MAX_QUEUE_DEPTH,
            "jobs_per_hour": RateLimits.JOBS_PER_HOUR,
            "jobs_per_day": RateLimits.JOBS_PER_DAY,
            "burst_limit": RateLimits.MAX_BURST_REQUESTS,
        },
        "active_ips": len(protection.ip_behaviors),
        "timestamp": time.time(),
    }
