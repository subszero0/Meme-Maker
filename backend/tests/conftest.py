"""
Pytest configuration for Meme Maker backend tests.

This file contains shared fixtures and configuration for all test modules.
"""

import os
import pytest


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end integration tests"
    )
    config.addinivalue_line(
        "markers", "smoke: marks tests as smoke tests (quick verification)"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running (> 30 seconds)"
    )


@pytest.fixture(scope="session")
def e2e_config():
    """
    E2E test configuration from environment variables.
    
    Returns a dictionary with test configuration values.
    """
    return {
        "base_url": os.environ.get("BASE_URL", "http://localhost:8000"),
        "test_video_url": os.environ.get(
            "TEST_VIDEO_URL", 
            "https://www.youtube.com/watch?v=BaW_jenozKc"
        ),
        "max_wait_timeout": int(os.environ.get("MAX_WAIT_TIMEOUT_SECONDS", "60")),
        "poll_interval": int(os.environ.get("POLL_INTERVAL_SECONDS", "2")),
        "min_clip_size": int(os.environ.get("MIN_CLIP_SIZE_BYTES", "10240")),  # 10KB
    }


@pytest.fixture(scope="session")
def skip_e2e():
    """
    Skip E2E tests if SKIP_E2E environment variable is set.
    
    Useful for CI environments where external dependencies aren't available.
    """
    if os.environ.get("SKIP_E2E", "").lower() in ("true", "1", "yes"):
        pytest.skip("E2E tests skipped via SKIP_E2E environment variable")


@pytest.fixture
def test_timeout():
    """Default timeout for individual test operations."""
    return int(os.environ.get("TEST_TIMEOUT_SECONDS", "30"))


@pytest.fixture
def mock_storage(monkeypatch):
    """
    Fixture to patch get_storage to return InMemoryStorage.
    
    Use this fixture in tests that need to mock storage operations.
    This is not autouse to avoid import issues with aioredis.
    
    Example:
        def test_something(mock_storage):
            # mock_storage is an InMemoryStorage instance
            # get_storage() will return this instance
            pass
    """
    from app.utils.mock_storage import InMemoryStorage
    from app.utils import reset_storage
    
    # Reset storage singleton to ensure clean state
    reset_storage()
    
    # Create a fresh InMemoryStorage instance for this test
    mock_storage_instance = InMemoryStorage()
    
    # Patch the get_storage function to return our mock
    monkeypatch.setattr('app.utils.get_storage', lambda: mock_storage_instance)
    
    yield mock_storage_instance
    
    # Clean up after the test
    mock_storage_instance.clear() 