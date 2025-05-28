from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# Security headers middleware (must be added before routers)
app.add_middleware(SecurityHeadersMiddleware)

# Include routers with proper tags and prefixes
app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])
app.include_router(metadata.router, prefix="/api/v1", tags=["metadata"])

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
