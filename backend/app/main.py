from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from .api import jobs, metadata
from .config import settings
from .middleware.security_headers import SecurityHeadersMiddleware
from . import metrics  # Import to register custom metrics

# Create FastAPI app
app = FastAPI(
    title="Meme Maker API",
    version="0.1.0",
    description="A tool to clip and download videos from social media platforms",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Initialize Prometheus instrumentator
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app, endpoint="/metrics")

# Security headers middleware (must be added before routers)
app.add_middleware(SecurityHeadersMiddleware)

# Include routers
app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])
app.include_router(metadata.router, prefix="/api/v1", tags=["metadata"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint"""
    return {"status": "ok"} 