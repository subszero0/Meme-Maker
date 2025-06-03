import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_health_check():
    """Test the health check endpoint"""
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_check_response_model():
    """Test that health check returns correct structure"""
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert isinstance(data["status"], str) 