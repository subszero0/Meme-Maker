"""Rate limiting functionality for the Meme Maker API"""

import os
from typing import Optional
import aioredis
from fastapi import HTTPException, Request, status
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from .config import settings

# Import metrics safely
try:
    from .metrics_definitions import RATE_DENIED
except ImportError:
    RATE_DENIED = None


async def init_rate_limit() -> None:
    """Initialize FastAPI rate limiter with Redis connection"""
    try:
        # Create async Redis connection for rate limiting
        redis = await aioredis.from_url(
            settings.redis_url, 
            encoding="utf-8", 
            decode_responses=True
        )
        
        # Initialize FastAPI limiter
        await FastAPILimiter.init(redis)
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
    return f"job_rate_limit:{client_ip}"


# Global rate limiter: 10 requests per minute for all API routes
global_limiter = RateLimiter(
    times=settings.global_rate_limit_requests,  # 10 requests
    seconds=settings.global_rate_limit_window,  # 60 seconds (1 minute)
    key_func=rate_limit_key_func
)

# Job creation rate limiter: 3 job creations per hour
job_creation_limiter = RateLimiter(
    times=settings.job_rate_limit_requests,  # 3 requests
    seconds=settings.job_rate_limit_window,  # 3600 seconds (1 hour)
    key_func=job_rate_limit_key_func
)

# Legacy limiter for backward compatibility (can be removed later)
clip_limiter = RateLimiter(
    times=40, 
    seconds=60*60*24,  # 24 hours
    key_func=rate_limit_key_func
)


async def rate_limit_exception_handler(request: Request, exc: HTTPException) -> dict:
    """Custom exception handler for rate limit errors"""
    # Increment rate limit denied metric if available
    if RATE_DENIED:
        RATE_DENIED.inc()
    
    # Log rate limit event for monitoring
    client_ip = get_client_ip(request)
    path = request.url.path
    print(f"Rate limit exceeded: IP={client_ip}, Path={path}")
    
    # Check if this is a rate limit exception
    if exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        retry_after = exc.headers.get("Retry-After", "60")  # Default to 1 minute
        retry_after_int = int(retry_after) if retry_after.isdigit() else 60
        
        # Determine rate limit type based on path
        if "/jobs" in path and request.method == "POST":
            detail_message = f"Job creation limit exceeded. You can create {settings.job_rate_limit_requests} jobs per hour. Please try again in {retry_after_int} seconds."
        else:
            detail_message = f"Rate limit exceeded. You can make {settings.global_rate_limit_requests} requests per minute. Please try again in {retry_after_int} seconds."
        
        return {
            "detail": detail_message,
            "retry_after": retry_after_int,
            "limit_type": "job_creation" if "/jobs" in path and request.method == "POST" else "global"
        }
    
    # For other exceptions, return original detail
    return {"detail": exc.detail} 