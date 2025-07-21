import os
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Try to import prometheus components, but continue if not available
try:
    from prometheus_fastapi_instrumentator import Instrumentator

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    print("Warning: prometheus_fastapi_instrumentator not available, metrics disabled")

from .api import clips, jobs, metadata
from .api import phase3_endpoints as admin
from .api import video_proxy
from .config import get_settings
from .middleware.admin_auth import AdminAuthMiddleware
from .middleware.queue_protection import QueueDosProtectionMiddleware
from .middleware.security_headers import SecurityHeadersMiddleware

# Get settings instance
settings = get_settings()

# Create FastAPI app with proper configuration
# SECURITY: Disable API documentation in production (CRIT-001)
docs_url = "/docs" if settings.environment != "production" else None
redoc_url = "/redoc" if settings.environment != "production" else None
openapi_url = "/openapi.json" if settings.environment != "production" else None

app = FastAPI(
    title="Meme Maker API",
    version="0.1.0",
    description="A tool to clip and download videos from social media platforms",
    docs_url=docs_url,  # Environment-aware documentation
    redoc_url=redoc_url,  # Environment-aware documentation
    openapi_url=openapi_url,  # Environment-aware OpenAPI spec
)

# Production service restart fix - July 9, 2025
# This change triggers CI/CD deployment to restart backend services that were returning 503 errors


# Custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log and return detailed validation errors."""
    # Log the full error detail for debugging
    error_messages = []
    for error in exc.errors():
        if isinstance(error.get("ctx", {}).get("error"), ValueError):
            error_messages.append(str(error["ctx"]["error"]))
        else:
            error_messages.append(error["msg"])

    print(f"❌ Validation error for {request.method} {request.url}: {error_messages}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation Error",
            "errors": error_messages,
        },
    )


# Custom exception handler for raw ValueErrors from Pydantic validators
@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    """Handle raw ValueErrors, returning a 422 response."""
    # Log the error for debugging
    print(f"❌ ValueError caught for {request.method} {request.url}: {exc}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )


# Startup validation
@app.on_event("startup")
async def startup_event():
    """Validate configuration and storage on startup"""
    # Initialize Redis connection synchronously
    from . import init_redis, redis

    print("🔍 Initializing Redis connection...")
    try:
        init_redis()
        # Test Redis connection immediately if it was initialized
        if redis is not None:
            # The init_redis function already logs success or fallback,
            # so we just need to test the connection if it exists.
            redis.ping()
            print("✅ Redis connection tested successfully.")
        # No 'else' needed here, as init_redis already warns if it falls back to FakeRedis.
    except Exception as e:
        print(f"❌ Redis connection test failed: {e}")
        # Don't fail startup, but log the issue

    # Ensure the clips directory exists, but don't crash on writability check
    clips_path = Path(settings.clips_dir)
    try:
        clips_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Clips directory ensured at: {clips_path}")
    except OSError as e:
        # This might happen in some CI environments with permission issues,
        # but we don't want to crash the entire application startup.
        # A failure to write a file later will be caught at runtime.
        print(
            f"⚠️ Could not create clips_dir ({clips_path}): {e}. Deferring error handling to runtime."
        )

    print(f"✅ Storage backend: {settings.storage_backend}")
    print("✅ Configuration validated successfully")


# Add CORS middleware with explicit configuration for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
    ]
    + (settings.cors_origins if isinstance(settings.cors_origins, list) else []),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Cache-Control",
        "Pragma",
        "User-Agent",
    ],
    expose_headers=["*"],
)

# Initialize Prometheus instrumentator if available
if PROMETHEUS_AVAILABLE:
    instrumentator = Instrumentator()
    instrumentator.instrument(app).expose(app, endpoint="/metrics")
    
    # Import and initialize custom metrics at startup
    try:
        from .metrics import clip_jobs_queued_total, clip_jobs_inflight, clip_job_latency_seconds
        # Initialize metrics with zero values to make them appear in the registry
        clip_jobs_queued_total._value._value = 0  # Initialize counter
        clip_jobs_inflight.set(0)                 # Initialize gauge
        # Latency histogram will appear after first use
        print("✅ Custom Prometheus metrics loaded and initialized successfully")
    except ImportError as e:
        print(f"❌ Failed to import custom metrics: {e}")
    except Exception as e:
        print(f"⚠️ Custom metrics loaded but initialization had issues: {e}")

# 🚨 T-003 QUEUE DOS PROTECTION MIDDLEWARE (Critical)
app.add_middleware(QueueDosProtectionMiddleware)

# 🚨 CRIT-002: Admin authentication middleware (Critical)
app.add_middleware(AdminAuthMiddleware, admin_api_key=settings.admin_api_key)

# Security headers middleware (must be added before routers)
app.add_middleware(SecurityHeadersMiddleware)

# Include routers with proper tags and prefixes
app.include_router(clips.router, prefix="/api/v1", tags=["clips"])
app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])
app.include_router(metadata.router, prefix="/api/v1", tags=["metadata"])
app.include_router(video_proxy.router, prefix="/api/v1/video", tags=["video-proxy"])
app.include_router(admin.router, tags=["admin"])  # Admin endpoints with authentication


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint"""
    # Returns a simple JSON response to indicate the service is alive.
    return {"status": "ok"}


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    """Root endpoint with API information"""
    # Updated: 2025-06-30 - Ensure latest deployment with /metadata/extract endpoint
    return {
        "message": "Meme Maker API",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/debug/cors", tags=["debug"])
async def debug_cors() -> dict:
    """Debug endpoint to check CORS configuration"""
    return {
        "cors_origins": settings.cors_origins,
        "debug": settings.debug,
        "environment_variables": {
            "CORS_ORIGINS": os.getenv("CORS_ORIGINS", "Not set"),
            "DEBUG": os.getenv("DEBUG", "Not set"),
        },
        "middleware_info": "CORS middleware should allow requests from configured origins",
    }


@app.get("/debug/redis", tags=["debug"])
async def debug_redis() -> dict:
    """Debug endpoint to check Redis connection status"""
    from . import init_redis, redis

    # Try to initialize Redis if not already done
    if redis is None:
        try:
            init_redis()
        except Exception as e:
            return {
                "redis_status": "initialization_failed",
                "error": str(e),
                "redis_object": str(type(redis)),
            }

    # Test Redis connection
    try:
        if redis is not None:
            redis.ping()
            return {
                "redis_status": "connected",
                "redis_object": str(type(redis)),
                "ping_successful": True,
            }
        else:
            return {
                "redis_status": "not_initialized",
                "redis_object": str(type(redis)),
                "ping_successful": False,
            }
    except Exception as e:
        return {
            "redis_status": "connection_failed",
            "redis_object": str(type(redis)),
            "ping_successful": False,
            "error": str(e),
        }


@app.get("/api/v1/storage/metrics", tags=["monitoring"])
async def get_storage_metrics():
    """Get storage usage metrics for monitoring"""
    from .storage import LocalStorageManager
    from .storage_factory import storage_manager

    if isinstance(storage_manager, LocalStorageManager):
        stats = storage_manager.get_storage_stats()
        return {
            "storage_backend": settings.storage_backend,
            "clips_disk_used_bytes": stats["total_size_bytes"],
            "clips_disk_used_mb": stats["total_size_mb"],
            "file_count": stats["file_count"],
            "base_path": stats["base_path"],
        }
    else:
        return {
            "storage_backend": settings.storage_backend,
            "message": "Storage metrics not available",
        }
