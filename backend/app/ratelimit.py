"""Rate limiting functionality for the Meme Maker API"""

import math
from typing import Any, Dict, Optional

import redis.asyncio as redis
from fastapi import HTTPException, Request, status
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

from .config import settings

# Import metrics safely
rate_denied_metric: Optional[Any] = None
try:
    from .metrics_definitions import RATE_DENIED
    from prometheus_client import Counter
    rate_denied_metric = RATE_DENIED
except ImportError:
    pass  # rate_denied_metric remains None


async def init_rate_limit() -> None:
    """Initialize FastAPI rate limiter with Redis connection"""
    # Skip rate limiting in debug mode or when explicitly disabled
    if settings.debug or settings.rate_limit.lower() == "off":
        print("Rate limiting disabled (debug mode or RATE_LIMIT=off)")
        return

    try:
        # Create async Redis connection for rate limiting
        redis_client: redis.Redis = redis.from_url(  # type: ignore
            settings.redis_url, encoding="utf-8", decode_responses=True
        )

        # Initialize FastAPI limiter
        await FastAPILimiter.init(redis_client)
        print("Rate limiting initialized successfully")

    except Exception as e:
        print(f"Warning: Failed to initialize rate limiting: {str(e)}")
        raise


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies properly"""
    # Check for real IP header from load balancer/proxy
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain (original client)
        return forwarded_for.split(",")[0].strip()

    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fallback to direct connection IP
    return request.client.host if request.client else "unknown"


def rate_limit_key_func(request: Request) -> str:
    """Generate rate limit key based on client IP for global limits"""
    client_ip = get_client_ip(request)
    return f"global_rate_limit:{client_ip}"


def job_rate_limit_key_func(request: Request) -> str:
    """Generate rate limit key for job creation limits"""
    client_ip = get_client_ip(request)
    return f"job_create:{client_ip}"


def create_job_limiter() -> Optional[RateLimiter]:
    """Create job creation rate limiter with configurable limits"""
    # Skip rate limiting in debug mode or when explicitly disabled
    if settings.debug or settings.rate_limit.lower() == "off":
        return None

    try:
        # Calculate requests per minute from hourly limit (round up)
        requests_per_minute = math.ceil(settings.max_jobs_per_hour / 60)

        # Create RateLimiter compatible with fastapi-limiter 0.1.6
        return RateLimiter(times=requests_per_minute, seconds=60)
    except Exception as e:
        print(f"Warning: Failed to create job limiter: {e}")
        return None


# Global rate limiter: 10 requests per minute for all API routes
try:
    global_limiter: Optional[RateLimiter] = RateLimiter(
        times=settings.global_rate_limit_requests,  # 10 requests
        seconds=settings.global_rate_limit_window,  # 60 seconds (1 minute)
    )
except Exception as e:
    print(f"Warning: Failed to create global limiter: {e}")
    global_limiter = None

# Create job creation limiter with configurable limits
job_creation_limiter: Optional[RateLimiter] = create_job_limiter()

# Legacy limiter for backward compatibility (can be removed later)
try:
    clip_limiter: Optional[RateLimiter] = RateLimiter(times=40, seconds=60 * 60 * 24)  # 24 hours
except Exception as e:
    print(f"Warning: Failed to create clip limiter: {e}")
    clip_limiter = None


async def rate_limit_exception_handler(request: Request, exc: HTTPException) -> Dict[str, Any]:
    """Custom exception handler for rate limit errors"""
    # Increment rate limit denied metric if available
    if rate_denied_metric:
        rate_denied_metric.inc()

    # Log rate limit event for monitoring
    client_ip = get_client_ip(request)
    path = request.url.path
    print(f"Rate limit exceeded: IP={client_ip}, Path={path}")

    # Check if this is a rate limit exception
    if exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        retry_after_header = exc.headers.get("Retry-After", "60") if exc.headers else "60"
        retry_after = retry_after_header if retry_after_header else "60"
        retry_after_int = int(retry_after) if retry_after.isdigit() else 60

        # Determine rate limit type based on path
        if "/jobs" in path and request.method == "POST":
            detail_message = (
                f"Job creation limit reached – you can create up to "
                f"{settings.max_jobs_per_hour} clips per hour. "
                f"Wait {retry_after_int} s."
            )
        else:
            detail_message = (
                f"Rate limit exceeded. You can make "
                f"{settings.global_rate_limit_requests} requests per minute. "
                f"Please try again in {retry_after_int} seconds."
            )

        return {
            "detail": detail_message,
            "retry_after": retry_after_int,
            "limit_type": (
                "job_creation"
                if "/jobs" in path and request.method == "POST"
                else "global"
            ),
        }

    # For other exceptions, return original detail
    return {"detail": exc.detail}
