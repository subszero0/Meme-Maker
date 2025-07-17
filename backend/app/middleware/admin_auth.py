"""
Administrative endpoint authentication middleware.
Secures /api/v1/admin/* endpoints with API key authentication.
"""

import os
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..logging.config import get_logger

logger = get_logger(__name__)


class AdminAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to secure administrative endpoints with API key authentication.

    Protects all endpoints under /api/v1/admin/* with Bearer token authentication.
    """

    def __init__(self, app, admin_api_key: str = None):
        super().__init__(app)
        self.admin_api_key = admin_api_key or os.getenv("ADMIN_API_KEY")

        if not self.admin_api_key:
            logger.warning(
                "ADMIN_API_KEY not set - admin endpoints will be unprotected!"
            )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Check authentication for admin endpoints.
        """
        # Check if this is an admin endpoint
        if request.url.path.startswith("/api/v1/admin/"):
            if not self.admin_api_key:
                # If no API key is configured, deny access for security
                logger.error("Admin endpoint accessed but ADMIN_API_KEY not configured")
                return JSONResponse(
                    status_code=503,
                    content={
                        "detail": "Administrative endpoints are temporarily unavailable"
                    },
                )

            # Check for Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                client_host = request.client.host if request.client else "unknown"
                logger.warning(f"Unauthorized admin access attempt from {client_host}")
                return JSONResponse(
                    status_code=401,
                    content={
                        "detail": "Admin authentication required. Use 'Authorization: Bearer <api-key>' header"
                    },
                )

            # Validate Bearer token format
            if not auth_header.startswith("Bearer "):
                client_host = request.client.host if request.client else "unknown"
                logger.warning(f"Invalid auth format from {client_host}")
                return JSONResponse(
                    status_code=401,
                    content={
                        "detail": "Invalid authorization format. Use 'Authorization: Bearer <api-key>'"
                    },
                )

            # Extract and validate API key
            provided_key = auth_header[7:]  # Remove "Bearer " prefix
            if provided_key != self.admin_api_key:
                client_host = request.client.host if request.client else "unknown"
                logger.warning(f"Invalid admin API key from {client_host}")
                return JSONResponse(
                    status_code=403, content={"detail": "Invalid admin credentials"}
                )

            client_host = request.client.host if request.client else "unknown"
            logger.info(f"Successful admin authentication from {client_host}")

        # Process the request
        response = await call_next(request)
        return response
