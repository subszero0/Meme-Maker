import os
import requests
import pytest

# Best practice: run this after each deploy to confirm live system is responding as expected

@pytest.mark.e2e
@pytest.mark.skip(reason="E2E test for deployed environments only - run manually with pytest -m e2e")
def test_health_endpoint():
    base = os.getenv("E2E_BASE", "https://memeit.pro")
    r = requests.get(f"{base}/health", timeout=3)
    assert r.status_code == 200
    assert r.json()["status"] == "ok" 