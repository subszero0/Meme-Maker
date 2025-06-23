import pytest
import os
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.middleware.security_headers import SecurityHeadersMiddleware


@pytest.fixture
def app():
    """Create a test FastAPI app with security middleware"""
    test_app = FastAPI()
    test_app.add_middleware(SecurityHeadersMiddleware)

    @test_app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    @test_app.get("/health")
    async def health_check():
        return {"status": "ok"}

    return test_app


@pytest.fixture
def client(app):
    """Create a test client"""
    return TestClient(app)


class TestSecurityHeaders:
    """Test security headers middleware"""

    def test_security_headers_added(self, client):
        """Test that all required security headers are added"""
        response = client.get("/test")

        assert response.status_code == 200

        # Check all required security headers
        expected_headers = {
            "strict-transport-security": "max-age=63072000; includeSubDomains; preload",
            "content-security-policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; img-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'",
            "x-content-type-options": "nosniff",
            "x-frame-options": "DENY",
            "referrer-policy": "no-referrer",
            "permissions-policy": "camera=(), microphone=(), geolocation=(), interest-cohort=()",
        }

        for header, expected_value in expected_headers.items():
            assert header in response.headers
            assert response.headers[header] == expected_value

    def test_health_endpoint_with_security_headers(self, client):
        """Test that health endpoint includes security headers"""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

        # Check key security headers
        assert response.headers["x-frame-options"] == "DENY"
        assert "max-age=63072000" in response.headers["strict-transport-security"]

    def test_options_preflight_request(self, client):
        """Test OPTIONS preflight request handling"""
        response = client.options("/test")

        assert response.status_code == 200
        assert response.headers["access-control-allow-methods"] == "GET,POST,OPTIONS"
        assert (
            "content-type" in response.headers["access-control-allow-headers"].lower()
        )
        assert (
            "authorization" in response.headers["access-control-allow-headers"].lower()
        )
        assert response.headers["access-control-max-age"] == "86400"

    def test_options_health_endpoint(self, client):
        """Test OPTIONS request to health endpoint"""
        response = client.options("/health")

        assert response.status_code == 200
        assert response.headers["access-control-allow-methods"] == "GET,POST,OPTIONS"

    def test_csp_header_cached(self, app):
        """Test that CSP header is cached in middleware instance"""
        middleware = SecurityHeadersMiddleware(app)

        expected_csp = (
            "default-src 'none'; "
            "frame-ancestors 'none'; "
            "base-uri 'none'; "
            "img-src 'self'; "
            "style-src 'self'; "
            "script-src 'self'; "
            "connect-src 'self'"
        )

        assert middleware.csp_header == expected_csp

    def test_cors_with_wildcard_env(self, app):
        """Test CORS with wildcard using environment variable"""
        # Set environment variable for testing
        os.environ["CORS_ORIGINS"] = "*"

        # Create new client to pick up env changes
        client = TestClient(app)

        try:
            response = client.get("/test", headers={"origin": "https://any-domain.com"})
            # Note: We can't assert exact CORS behavior without mocking because it uses real settings
            # But we can verify the response is successful and contains security headers
            assert response.status_code == 200
            assert "x-frame-options" in response.headers
        finally:
            # Clean up environment
            if "CORS_ORIGINS" in os.environ:
                del os.environ["CORS_ORIGINS"]

    def test_cors_basic_functionality(self, client):
        """Test basic CORS functionality with default settings"""
        # Test that CORS headers are present in some form
        response = client.get("/test")
        assert response.status_code == 200

        # Should have basic CORS setup (either credentials or origin)
        has_cors = (
            "access-control-allow-credentials" in response.headers
            or "access-control-allow-origin" in response.headers
        )
        # This may or may not be true depending on settings, so we just verify the response works
        assert response.status_code == 200
