from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import os

# Try to import prometheus components, but continue if not available
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    print("Warning: prometheus_fastapi_instrumentator not available, metrics disabled")

from .api import jobs, metadata
from .config import settings
from .middleware.security_headers import SecurityHeadersMiddleware
from . import metrics  # Import to register custom metrics
from .metrics import start_queue_metrics_updater
from .ratelimit import init_rate_limit, rate_limit_exception_handler

# Create FastAPI app with proper configuration
app = FastAPI(
    title="Meme Maker API",
    version="0.1.0",
    description="A tool to clip and download videos from social media platforms",
    docs_url="/docs",  # Explicitly enable Swagger UI
    redoc_url="/redoc",  # Enable ReDoc as well
    openapi_url="/openapi.json",  # Ensure OpenAPI spec is available
)

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
    
    # Start the queue metrics updater
    start_queue_metrics_updater()

# Security headers middleware (must be added before routers)
app.add_middleware(SecurityHeadersMiddleware)

@app.on_event("startup")
async def startup():
    """Initialize rate limiting on startup"""
    try:
        await init_rate_limit()
    except Exception as e:
        print(f"Warning: Rate limiting initialization failed: {str(e)}")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Custom exception handler for rate limiting and other HTTP errors"""
    # Handle rate limit exceptions specially
    if exc.status_code == 429:
        response_data = await rate_limit_exception_handler(request, exc)
        return JSONResponse(
            status_code=429,
            content=response_data,
            headers={"Retry-After": str(response_data.get("retry_after", 3600))}
        )
    
    # For other HTTP exceptions, return standard format
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Include routers with proper tags and prefixes
app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])
app.include_router(metadata.router, prefix="/api/v1", tags=["metadata"])

@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint"""
    return {"status": "ok"}

# Test endpoints for alert testing (only in development)
if settings.debug:
    @app.get("/test-error", tags=["testing"])
    async def test_error():
        """Test endpoint that always returns 500 error for alert testing"""
        raise HTTPException(status_code=500, detail="Test error for monitoring")
    
    @app.get("/test-timeout", tags=["testing"])
    async def test_timeout():
        """Test endpoint that simulates a timeout"""
        import time
        time.sleep(10)  # Simulate slow response
        return {"message": "Slow response"}

# Static files directory path
STATIC_DIR = Path("/app/static")

# Mount static files if directory exists
if STATIC_DIR.exists():
    # Mount the entire static directory at root to serve Next.js assets
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    
    @app.get("/{full_path:path}", tags=["frontend"])
    async def serve_frontend(full_path: str):
        """Serve frontend SPA for all non-API routes"""
        # Don't serve frontend for API routes, docs, or health
        if full_path.startswith(("api/", "docs", "redoc", "openapi.json", "health", "metrics", "static/")):
            raise HTTPException(status_code=404, detail=f"Path '{full_path}' not found")
        
        # Handle root path
        if not full_path or full_path == "":
            index_path = STATIC_DIR / "index.html"
            if index_path.is_file():
                return FileResponse(index_path, media_type="text/html")
        
        # Try to serve the requested file directly
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        
        # For SPA routing, serve index.html for all other routes
        index_path = STATIC_DIR / "index.html"
        if index_path.is_file():
            return FileResponse(index_path, media_type="text/html")
        
        raise HTTPException(status_code=404, detail="Frontend not available")
else:
    @app.get("/", tags=["root"])
    async def root() -> dict[str, str]:
        """Root endpoint with API information"""
        return {
            "message": "Meme Maker API",
            "version": "0.1.0",
            "docs": "/docs",
            "redoc": "/redoc"
        }
