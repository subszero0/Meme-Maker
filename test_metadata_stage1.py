#!/usr/bin/env python3
"""
Test Script: Stage 1 - Basic Metadata Extraction
================================================================

This script tests the basic metadata endpoint (/api/v1/metadata) to verify:
1. The endpoint is accessible
2. Request/response format is correct
3. Performance timing
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_URL = "https://www.youtube.com/watch?v=cqvjbDdiCCQ"

def test_basic_metadata():
    """Test the basic metadata extraction endpoint"""
    print(f"=== Stage 1: Basic Metadata Extraction Test ===")
    print(f"Timestamp: {datetime.now()}")
    print(f"Testing URL: {TEST_URL}")
    print(f"API Base: {API_BASE_URL}")
    print("")
    
    # Test data matching backend models exactly
    request_data = {
        "url": TEST_URL
    }
    
    print(f"1. Sending request to /api/v1/metadata")
    print(f"   Request payload: {json.dumps(request_data, indent=2)}")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/metadata",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"2. Response received in {duration:.2f} seconds")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS - Basic metadata extracted!")
            print(f"   Title: {data.get('title', 'N/A')}")
            print(f"   Duration: {data.get('duration', 'N/A')} seconds")
            print(f"   Resolutions: {data.get('resolutions', 'N/A')}")
            print(f"   Thumbnail: {data.get('thumbnail_url', 'N/A')}")
            return True
        else:
            print(f"❌ FAILED - HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        end_time = time.time()
        duration = end_time - start_time
        print(f"❌ TIMEOUT after {duration:.2f} seconds")
        return False
        
    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR - Is the backend running?")
        return False
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"❌ UNEXPECTED ERROR after {duration:.2f} seconds: {e}")
        return False

def test_health_first():
    """Test if backend is running"""
    print(f"0. Health Check")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Backend is running")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except:
        print(f"❌ Backend is not accessible")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("METADATA EXTRACTION - STAGE 1 TEST")
    print("=" * 60)
    
    if not test_health_first():
        print("\n🛑 Cannot proceed - backend not running")
        exit(1)
    
    print()
    success = test_basic_metadata()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ STAGE 1 PASSED - Basic metadata extraction working")
    else:
        print("❌ STAGE 1 FAILED - Basic metadata extraction broken")
    print("=" * 60) 