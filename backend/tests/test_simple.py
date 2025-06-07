"""
Simple test to verify basic imports and app creation work.
"""


from app.main import app


def test_app_creation():
    """Test that the FastAPI app can be created successfully"""
    assert app is not None
    assert app.title == "Meme Maker API"
    assert app.version == "0.1.0"


def test_health_endpoint_exists():
    """Test that the health endpoint is registered"""
    routes = [route.path for route in app.routes]
    assert "/health" in routes


def test_api_routes_exist():
    """Test that the main API routes are registered"""
    routes = [route.path for route in app.routes]

    # Check for API v1 routes
    api_routes = [route for route in routes if route.startswith("/api/v1")]
    assert len(api_routes) > 0, "API v1 routes should be registered"
