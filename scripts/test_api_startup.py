#!/usr/bin/env python3
"""
API Server Startup Test Script

This script tests the API server startup process and diagnoses common issues.
"""

import os
import sys
import time
import requests
import subprocess
from pathlib import Path


def check_dependencies():
    """Check if all required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    try:
        import fastapi
        print(f"  ✅ FastAPI: {fastapi.__version__}")
    except ImportError:
        print("  ❌ FastAPI not installed")
        return False
    
    try:
        import uvicorn
        print(f"  ✅ Uvicorn: {uvicorn.__version__}")
    except ImportError:
        print("  ❌ Uvicorn not installed") 
        return False
    
    try:
        import redis
        print(f"  ✅ Redis: {redis.__version__}")
    except ImportError:
        print("  ❌ Redis not installed")
        return False
    
    try:
        import fakeredis
        print(f"  ✅ FakeRedis: {fakeredis.__version__}")
    except ImportError:
        print("  ❌ FakeRedis not installed")
        return False
    
    return True


def check_environment():
    """Check environment configuration"""
    print("\n🔧 Checking environment configuration...")
    
    # Set minimal required environment variables
    env_vars = {
        "DEBUG": "true",
        "REDIS_URL": "redis://localhost:6379",
        "CORS_ORIGINS": "*",
        "AWS_ACCESS_KEY_ID": "test",
        "AWS_SECRET_ACCESS_KEY": "test", 
        "S3_BUCKET": "test-bucket"
    }
    
    for key, default_value in env_vars.items():
        value = os.environ.get(key, default_value)
        os.environ[key] = value
        print(f"  ✅ {key}={value}")


def test_api_import():
    """Test if the API module can be imported"""
    print("\n📦 Testing API module import...")
    
    try:
        from app.main import app
        print("  ✅ API module imported successfully")
        return app
    except ImportError as e:
        print(f"  ❌ Failed to import API module: {e}")
        return None
    except Exception as e:
        print(f"  ❌ Error importing API module: {e}")
        return None


def test_health_endpoint(base_url="http://localhost:8000", timeout=60):
    """Test the health endpoint"""
    print(f"\n🏥 Testing health endpoint at {base_url}/health...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ Health check passed: {data}")
                return True
            else:
                print(f"  ⚠️  Health check returned {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"  ⏳ Waiting for server... ({int(time.time() - start_time)}s)")
        except Exception as e:
            print(f"  ❌ Health check error: {e}")
        
        time.sleep(2)
    
    print(f"  ❌ Health check failed after {timeout}s timeout")
    return False


def main():
    """Run all startup tests"""
    print("🚀 API Server Startup Diagnostic")
    print("=" * 40)
    
    # Check if we're in the backend directory
    if not Path("app").exists():
        print("❌ Not in backend directory. Please run from backend/ folder.")
        sys.exit(1)
    
    # Step 1: Check dependencies
    if not check_dependencies():
        print("\n❌ Dependencies check failed")
        sys.exit(1)
    
    # Step 2: Check environment
    check_environment()
    
    # Step 3: Test import
    app = test_api_import()
    if not app:
        print("\n❌ API import failed")
        sys.exit(1)
    
    # Step 4: Test health endpoint (assumes server is running)
    base_url = os.environ.get("BASE_URL", "http://localhost:8000")
    if test_health_endpoint(base_url):
        print(f"\n✅ All tests passed! API server is running at {base_url}")
    else:
        print(f"\n❌ API server not responding at {base_url}")
        print("\n💡 Troubleshooting tips:")
        print("  1. Make sure the server is started with: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("  2. Check if Redis is running (if not using fakeredis)")
        print("  3. Verify all environment variables are set")
        print("  4. Check the server logs for startup errors")
        sys.exit(1)


if __name__ == "__main__":
    main() 