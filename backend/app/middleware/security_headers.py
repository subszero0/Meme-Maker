import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        
        # Cache CSP string to avoid rebuilding on each request
        # More permissive CSP for Swagger UI to work
        self.csp_header = (
            "default-src 'self'; "
            "img-src 'self' data: https:; "
            "style-src 'self' 'unsafe-inline' https:; "
            "script-src 'self' 'unsafe-inline' https:; "
            "font-src 'self' https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'"
        )
        
        # Development-friendly CSP that allows localhost HTTP connections
        self.dev_csp_header = (
            "default-src 'self'; "
            "img-src 'self' data: https: http://localhost:*; "
            "style-src 'self' 'unsafe-inline' https: http://localhost:*; "
            "script-src 'self' 'unsafe-inline' https: http://localhost:*; "
            "font-src 'self' https: http://localhost:*; "
            "connect-src 'self' https: http://localhost:* ws://localhost:*; "
            "frame-ancestors 'none'; "
            "base-uri 'self'"
        )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response"""
        
        # Import settings here to avoid circular imports and get current values
        from ..config import get_settings
        settings = get_settings()
        
        # Warn if CORS is set to allow all origins in production (only check once per request)
        if "*" in settings.cors_origins and not settings.debug and not hasattr(self, '_warned'):
            logger.warning("CORS is set to allow all origins (*) in production mode")
            self._warned = True
        
        # Handle preflight OPTIONS requests
        if request.method == "OPTIONS":
            response = Response()
            self._add_cors_headers(response, request, settings)
            response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response.headers["Access-Control-Max-Age"] = "86400"  # 24 hours
            return response
        
        response = await call_next(request)
        
        # Add security headers (but skip CSP for Swagger UI endpoints)
        self._add_security_headers(response, request)
        self._add_cors_headers(response, request, settings)
        
        return response
    
    def _add_security_headers(self, response: Response, request: Request) -> None:
        """Add all security headers to the response"""
        
        # Import settings here to avoid circular imports and get current values
        from ..config import get_settings
        settings = get_settings()
        
        # Skip ALL security headers for Swagger UI, ReDoc and OpenAPI endpoints
        swagger_paths = ["/docs", "/redoc", "/openapi.json"]
        if any(request.url.path.startswith(path) for path in swagger_paths):
            return
        
        # Also skip for any static resources that Swagger UI might need
        if "/swagger-ui" in request.url.path or "/redoc" in request.url.path:
            return
        
        # Use development-friendly CSP for local development
        csp_header = self.dev_csp_header if settings.debug else self.csp_header
        
        security_headers = {
            "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
            "Content-Security-Policy": csp_header,
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "no-referrer",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(), interest-cohort=()",
        }
        
        response.headers.update(security_headers)
    
    def _add_cors_headers(self, response: Response, request: Request, settings) -> None:
        """Add CORS headers based on settings"""
        origin = request.headers.get("origin")
        
        if "*" in settings.cors_origins:
            # Allow all origins
            response.headers["Access-Control-Allow-Origin"] = "*"
        elif origin and origin in settings.cors_origins:
            # Allow specific origin
            response.headers["Access-Control-Allow-Origin"] = origin
        elif len(settings.cors_origins) == 1 and not origin:
            # For same-origin requests, use the first configured origin
            response.headers["Access-Control-Allow-Origin"] = settings.cors_origins[0]
        
        # Add other CORS headers if we set an origin
        if "Access-Control-Allow-Origin" in response.headers:
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Vary"] = "Origin" 