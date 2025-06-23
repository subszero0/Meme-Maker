import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Try to import prometheus components, but continue if not available
try:
    from prometheus_fastapi_instrumentator import Instrumentator

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    print("Warning: prometheus_fastapi_instrumentator not available, metrics disabled")

from .api import clips, jobs, metadata
from .config import get_settings
from .middleware.security_headers import SecurityHeadersMiddleware

# Get settings instance
settings = get_settings()

# Create FastAPI app with proper configuration
app = FastAPI(
    title="Meme Maker API",
    version="0.1.0",
    description="A tool to clip and download videos from social media platforms",
    docs_url="/docs",  # Explicitly enable Swagger UI
    redoc_url="/redoc",  # Enable ReDoc as well
    openapi_url="/openapi.json",  # Ensure OpenAPI spec is available
)


# Startup validation
@app.on_event("startup")
async def startup_event():
    """Validate configuration and storage on startup"""
    # Initialize Redis connection synchronously
    from . import init_redis, redis

    print("🔍 Initializing Redis connection...")
    try:
        result = init_redis()
        # Test Redis connection immediately if it was initialized
        if redis is not None:
            redis.ping()
            print("✅ Redis connected and tested successfully")
        else:
            print("⚠️ Redis not available - running without cache")
    except Exception as e:
        print(f"❌ Redis initialization/test failed: {e}")
        # Don't fail startup, but log the issue

    # Fail fast if clips directory isn't writable
    clips_path = Path(settings.clips_dir)
    clips_path.mkdir(parents=True, exist_ok=True)

    if not os.access(clips_path, os.W_OK):
        raise RuntimeError(f"clips_dir not writable: {clips_path}")

    print(f"✅ Storage backend: {settings.storage_backend}")
    print(f"✅ Clips directory: {clips_path} (writable)")
    print(f"✅ Configuration validated successfully")


# Add CORS middleware with explicit configuration for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
    ]
    + settings.cors_origins,
    allow_credentials=False,  # Set to False for development to avoid credentials issues
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

# Security headers middleware (must be added before routers)
app.add_middleware(SecurityHeadersMiddleware)

# Include routers with proper tags and prefixes
app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])
app.include_router(metadata.router, prefix="/api/v1", tags=["metadata"])
app.include_router(clips.router, tags=["clips"])  # No prefix for direct /clips access


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    """Root endpoint with API information"""
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
