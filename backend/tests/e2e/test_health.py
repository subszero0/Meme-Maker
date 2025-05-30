import os
import requests

# Best practice: run this after each deploy to confirm live system is responding as expected

def test_health_endpoint():
    base = os.getenv("E2E_BASE", "https://memeit.pro")
    r = requests.get(f"{base}/health", timeout=3)
    assert r.status_code == 200
    assert r.json()["status"] == "ok" 