"""
Rate limiting middleware using token bucket algorithm.
Implements per-IP and per-endpoint rate limiting for API security.
"""
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..config.configuration import get_settings
from ..constants import RateLimits
from ..logging.config import get_logger

logger = get_logger(__name__)


@dataclass
class TokenBucket:
    """Token bucket for rate limiting"""

    capacity: int
    tokens: float
    refill_rate: float  # tokens per second
    last_refill: float

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from the bucket"""
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def _refill(self):
        """Refill tokens based on time elapsed"""
        now = time.time()
        elapsed = now - self.last_refill

        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now


class RateLimiter:
    """
    Rate limiter using token bucket algorithm.
    Supports per-IP and per-endpoint rate limiting.
    """

    def __init__(self):
        self.settings = get_settings()

        # Per-IP rate limiting buckets
        self.ip_buckets: Dict[str, TokenBucket] = {}

        # Per-endpoint rate limiting buckets
        self.endpoint_buckets: Dict[str, Dict[str, TokenBucket]] = defaultdict(dict)

        # Rate limit configurations
        self.rate_limits = {
            # Global rate limits (per IP)
            "global": {
                "capacity": RateLimits.REQUESTS_PER_MINUTE,
                "refill_rate": RateLimits.REQUESTS_PER_MINUTE / 60.0,  # per second
            },
            # Endpoint-specific rate limits
            "/api/v1/jobs": {
                "capacity": RateLimits.JOBS_PER_HOUR,
                "refill_rate": RateLimits.JOBS_PER_HOUR / 3600.0,
            },
            "/api/v1/metadata": {
                "capacity": RateLimits.METADATA_REQUESTS_PER_MINUTE,
                "refill_rate": RateLimits.METADATA_REQUESTS_PER_MINUTE / 60.0,
            },
        }

        # Cleanup task
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes

    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers first (for proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"

    def get_endpoint_key(self, request: Request) -> str:
        """Generate endpoint key for rate limiting"""
        # Use path pattern for endpoint identification
        path = request.url.path

        # Normalize path for rate limiting (remove dynamic segments)
        for pattern in self.rate_limits.keys():
            if pattern != "global" and path.startswith(pattern):
                return pattern

        return path

    def _get_or_create_bucket(
        self, bucket_dict: Dict[str, TokenBucket], key: str, config: Dict[str, float]
    ) -> TokenBucket:
        """Get existing bucket or create new one"""
        if key not in bucket_dict:
            bucket_dict[key] = TokenBucket(
                capacity=int(config["capacity"]),
                tokens=float(config["capacity"]),
                refill_rate=config["refill_rate"],
                last_refill=time.time(),
            )

        return bucket_dict[key]

    async def check_rate_limit(
        self, request: Request
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if request should be rate limited

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        client_ip = self.get_client_ip(request)
        endpoint = self.get_endpoint_key(request)

        # Check global IP-based rate limit
        global_config = self.rate_limits["global"]
        ip_bucket = self._get_or_create_bucket(
            self.ip_buckets, client_ip, global_config
        )

        if not ip_bucket.consume():
            return False, {
                "limit_type": "global",
                "limit": global_config["capacity"],
                "remaining": int(ip_bucket.tokens),
                "reset_in": self._calculate_reset_time(ip_bucket, global_config),
                "client_ip": client_ip,
            }

        # Check endpoint-specific rate limit
        if endpoint in self.rate_limits:
            endpoint_config = self.rate_limits[endpoint]
            endpoint_key = f"{client_ip}:{endpoint}"

            endpoint_bucket = self._get_or_create_bucket(
                self.endpoint_buckets[endpoint], endpoint_key, endpoint_config
            )

            if not endpoint_bucket.consume():
                return False, {
                    "limit_type": "endpoint",
                    "endpoint": endpoint,
                    "limit": endpoint_config["capacity"],
                    "remaining": int(endpoint_bucket.tokens),
                    "reset_in": self._calculate_reset_time(
                        endpoint_bucket, endpoint_config
                    ),
                    "client_ip": client_ip,
                }

        # Periodic cleanup
        await self._cleanup_old_buckets()

        return True, None

    def _calculate_reset_time(
        self, bucket: TokenBucket, config: Dict[str, float]
    ) -> int:
        """Calculate time until bucket is fully refilled"""
        if bucket.tokens >= config["capacity"]:
            return 0

        tokens_needed = config["capacity"] - bucket.tokens
        return int(tokens_needed / config["refill_rate"])

    async def _cleanup_old_buckets(self):
        """Clean up old unused buckets to prevent memory leaks"""
        now = time.time()

        # Only run cleanup periodically
        if now - self._last_cleanup < self._cleanup_interval:
            return

        self._last_cleanup = now

        # Clean up IP buckets older than 1 hour
        cutoff_time = now - 3600

        old_ip_keys = [
            key
            for key, bucket in self.ip_buckets.items()
            if bucket.last_refill < cutoff_time
        ]

        for key in old_ip_keys:
            del self.ip_buckets[key]

        # Clean up endpoint buckets
        for endpoint, buckets in self.endpoint_buckets.items():
            old_endpoint_keys = [
                key
                for key, bucket in buckets.items()
                if bucket.last_refill < cutoff_time
            ]

            for key in old_endpoint_keys:
                del buckets[key]

        if old_ip_keys or any(
            old_endpoint_keys
            for old_endpoint_keys in [
                buckets for buckets in self.endpoint_buckets.values()
            ]
        ):
            logger.debug(
                f"Cleaned up {len(old_ip_keys)} IP buckets and endpoint buckets"
            )

    def get_rate_limit_info(self, request: Request) -> Dict[str, Any]:
        """Get current rate limit status for client"""
        client_ip = self.get_client_ip(request)
        endpoint = self.get_endpoint_key(request)

        info = {
            "client_ip": client_ip,
            "endpoint": endpoint,
            "global_limit": self.rate_limits["global"],
            "endpoint_limit": self.rate_limits.get(endpoint, "No specific limit"),
        }

        # Add current bucket status
        if client_ip in self.ip_buckets:
            bucket = self.ip_buckets[client_ip]
            info["global_tokens_remaining"] = int(bucket.tokens)

        endpoint_key = f"{client_ip}:{endpoint}"
        if (
            endpoint in self.endpoint_buckets
            and endpoint_key in self.endpoint_buckets[endpoint]
        ):
            bucket = self.endpoint_buckets[endpoint][endpoint_key]
            info["endpoint_tokens_remaining"] = int(bucket.tokens)

        return info


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""

    def __init__(self, app, rate_limiter: Optional[RateLimiter] = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()

        # Excluded paths (health checks, metrics, etc.)
        self.excluded_paths = {
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        }

    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiter"""
        # Skip rate limiting for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Check rate limit
        is_allowed, rate_limit_info = await self.rate_limiter.check_rate_limit(request)

        if not is_allowed:
            # Log rate limit hit
            logger.warning(
                f"Rate limit exceeded for {rate_limit_info['client_ip']} "
                f"on {rate_limit_info.get('endpoint', 'global')} "
                f"(limit: {rate_limit_info['limit']}, remaining: {rate_limit_info['remaining']})"
            )

            # Return rate limit error
            error_response = {
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Try again in {rate_limit_info['reset_in']} seconds.",
                "limit_type": rate_limit_info["limit_type"],
                "limit": rate_limit_info["limit"],
                "remaining": rate_limit_info["remaining"],
                "reset_in_seconds": rate_limit_info["reset_in"],
            }

            headers = {
                "X-RateLimit-Limit": str(rate_limit_info["limit"]),
                "X-RateLimit-Remaining": str(rate_limit_info["remaining"]),
                "X-RateLimit-Reset": str(
                    int(time.time()) + rate_limit_info["reset_in"]
                ),
                "Retry-After": str(rate_limit_info["reset_in"]),
            }

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=error_response,
                headers=headers,
            )

        # Process request normally
        response = await call_next(request)

        # Add rate limit headers to successful responses
        client_ip = self.rate_limiter.get_client_ip(request)

        if client_ip in self.rate_limiter.ip_buckets:
            bucket = self.rate_limiter.ip_buckets[client_ip]
            config = self.rate_limiter.rate_limits["global"]

            response.headers["X-RateLimit-Limit"] = str(config["capacity"])
            response.headers["X-RateLimit-Remaining"] = str(int(bucket.tokens))
            response.headers["X-RateLimit-Reset"] = str(
                int(time.time())
                + self.rate_limiter._calculate_reset_time(bucket, config)
            )

        return response


# Dependency for getting rate limiter instance
def get_rate_limiter() -> RateLimiter:
    """Dependency to get rate limiter instance"""
    return RateLimiter()


# Utility functions
async def check_specific_rate_limit(
    request: Request, rate_limiter: RateLimiter, limit: int, window_seconds: int
) -> bool:
    """
    Check a specific rate limit for custom use cases

    Args:
        request: FastAPI request object
        rate_limiter: RateLimiter instance
        limit: Number of requests allowed
        window_seconds: Time window in seconds

    Returns:
        True if allowed, False if rate limited
    """
    # This would implement custom rate limiting logic
    # For now, delegate to the standard rate limiter
    is_allowed, _ = await rate_limiter.check_rate_limit(request)
    return is_allowed


def create_rate_limit_response(rate_limit_info: Dict[str, Any]) -> JSONResponse:
    """Create a standardized rate limit response"""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Try again in {rate_limit_info['reset_in']} seconds.",
            "details": rate_limit_info,
        },
        headers={"Retry-After": str(rate_limit_info["reset_in"])},
    )
