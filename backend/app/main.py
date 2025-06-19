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

from .api import jobs, metadata, clips
from .config import settings
from .middleware.security_headers import SecurityHeadersMiddleware
from . import metrics  # Import to register custom metrics

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
    # Fail fast if clips directory isn't writable
    clips_path = Path(settings.clips_dir)
    clips_path.mkdir(parents=True, exist_ok=True)
    
    if not os.access(clips_path, os.W_OK):
        raise RuntimeError(f"clips_dir not writable: {clips_path}")
    
    print(f"✅ Storage backend: {settings.storage_backend}")
    print(f"✅ Clips directory: {clips_path} (writable)")
    print(f"✅ Configuration validated successfully")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        "redoc": "/redoc"
    }

@app.get("/debug/cors", tags=["debug"])
async def debug_cors() -> dict:
    """Debug endpoint to check CORS configuration"""
    from .config import settings
    return {
        "cors_origins": settings.cors_origins,
        "debug": settings.debug,
        "environment_variables": {
            "CORS_ORIGINS": os.getenv("CORS_ORIGINS", "Not set"),
            "DEBUG": os.getenv("DEBUG", "Not set")
        }
    }

@app.get("/api/v1/storage/metrics", tags=["monitoring"])
async def get_storage_metrics():
    """Get storage usage metrics for monitoring"""
    from .storage_factory import storage_manager
    from .storage import LocalStorageManager
    
    if isinstance(storage_manager, LocalStorageManager):
        stats = storage_manager.get_storage_stats()
        return {
            "storage_backend": settings.storage_backend,
            "clips_disk_used_bytes": stats["total_size_bytes"],
            "clips_disk_used_mb": stats["total_size_mb"],
            "file_count": stats["file_count"],
            "base_path": stats["base_path"]
        }
    else:
        return {
            "storage_backend": settings.storage_backend,
            "message": "Storage metrics not available for S3 backend"
        }
