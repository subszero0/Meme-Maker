#!/usr/bin/env python3
"""
Comprehensive Error Testing Script
Following Best Practice #14: Create multiple scripts/tests for each stage
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
TEST_VIDEO_URL = "https://www.youtube.com/watch?v=TzUWcoI9TpA"

def print_stage(stage_name, description=""):
    print(f"\n{'='*60}")
    print(f"🧪 STAGE: {stage_name}")
    if description:
        print(f"📋 {description}")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print('='*60)

def test_stage_1_container_health():
    """Test if Docker containers are running and healthy"""
    print_stage("CONTAINER HEALTH", "Checking if all Docker containers are running")
    
    try:
        import subprocess
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        if result.returncode == 0:
            containers = result.stdout
            required_containers = [
                'meme-maker-backend-dev',
                'meme-maker-frontend-dev', 
                'meme-maker-worker-dev',
                'meme-maker-redis-dev'
            ]
            
            all_running = True
            for container in required_containers:
                if container in containers:
                    print(f"✅ {container}: RUNNING")
                else:
                    print(f"❌ {container}: NOT FOUND")
                    all_running = False
            
            return all_running
        else:
            print("❌ Failed to check Docker containers")
            return False
    except Exception as e:
        print(f"❌ Error checking containers: {e}")
        return False

def test_stage_2_backend_health():
    """Test backend health endpoint"""
    print_stage("BACKEND HEALTH", "Testing backend /health endpoint")
    
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend health: {data}")
            return True
        else:
            print(f"❌ Backend health failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend health error: {e}")
        return False

def test_stage_3_cors_headers():
    """Test CORS headers are properly configured"""
    print_stage("CORS CONFIGURATION", "Testing CORS headers on API endpoints")
    
    try:
        response = requests.options(f"{BACKEND_URL}/api/v1/metadata", 
                                  headers={'Origin': 'http://localhost:3000'})
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        }
        
        print(f"📡 CORS Headers: {json.dumps(cors_headers, indent=2)}")
        
        if 'Access-Control-Allow-Origin' in response.headers:
            print("✅ CORS properly configured")
            return True
        else:
            print("❌ CORS not configured")
            return False
    except Exception as e:
        print(f"❌ CORS test error: {e}")
        return False

def test_stage_4_metadata_endpoint():
    """Test basic metadata endpoint"""
    print_stage("METADATA API", "Testing /api/v1/metadata endpoint")
    
    try:
        payload = {"url": TEST_VIDEO_URL}
        response = requests.post(f"{BACKEND_URL}/api/v1/metadata", 
                               json=payload, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📊 Response Time: {response.elapsed.total_seconds():.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Metadata: {data['title'][:50]}...")
            print(f"✅ Duration: {data['duration']}s")
            print(f"✅ Resolutions: {data.get('resolutions', [])}")
            return True
        else:
            print(f"❌ Metadata failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Metadata error: {e}")
        return False

def test_stage_5_detailed_metadata():
    """Test detailed metadata endpoint"""
    print_stage("DETAILED METADATA", "Testing /api/v1/metadata/extract endpoint")
    
    try:
        payload = {"url": TEST_VIDEO_URL}
        response = requests.post(f"{BACKEND_URL}/api/v1/metadata/extract", 
                               json=payload, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📊 Response Time: {response.elapsed.total_seconds():.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Title: {data['title'][:50]}...")
            print(f"✅ Formats available: {len(data.get('formats', []))}")
            return True
        else:
            print(f"❌ Detailed metadata failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Detailed metadata error: {e}")
        return False

def test_stage_6_job_creation():
    """Test job creation endpoint"""
    print_stage("JOB CREATION", "Testing /api/v1/jobs endpoint")
    
    try:
        payload = {
            "url": TEST_VIDEO_URL,
            "in_ts": 10,
            "out_ts": 20,
            "format_id": "18"
        }
        response = requests.post(f"{BACKEND_URL}/api/v1/jobs", 
                               json=payload, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            job_id = data['id']
            print(f"✅ Job created: {job_id}")
            print(f"✅ Status: {data['status']}")
            return job_id
        else:
            print(f"❌ Job creation failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Job creation error: {e}")
        return False

def test_stage_7_frontend_access():
    """Test if frontend is accessible"""
    print_stage("FRONTEND ACCESS", "Testing if frontend is serving content")
    
    try:
        response = requests.get(f"{FRONTEND_URL}", timeout=5)
        if response.status_code == 200:
            print(f"✅ Frontend accessible: {response.status_code}")
            print(f"📊 Content type: {response.headers.get('content-type')}")
            return True
        else:
            print(f"❌ Frontend not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend access error: {e}")
        return False

def run_all_tests():
    """Run all test stages and report results"""
    print(f"\n🚀 STARTING COMPREHENSIVE ERROR TESTING")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Run all test stages
    results['containers'] = test_stage_1_container_health()
    results['backend_health'] = test_stage_2_backend_health()
    results['cors'] = test_stage_3_cors_headers()
    results['metadata'] = test_stage_4_metadata_endpoint()
    results['detailed_metadata'] = test_stage_5_detailed_metadata()
    results['job_creation'] = test_stage_6_job_creation()
    results['frontend'] = test_stage_7_frontend_access()
    
    # Summary report
    print(f"\n{'='*60}")
    print("📊 FINAL RESULTS SUMMARY")
    print('='*60)
    
    passed = 0
    total = len(results)
    
    for stage, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{stage.upper():<20}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Score: {passed}/{total} stages passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - System appears healthy!")
    else:
        print("⚠️  SOME TESTS FAILED - Investigation needed")
        
    return results

if __name__ == "__main__":
    results = run_all_tests()
    
    # Exit with error code if any tests failed
    if not all(results.values()):
        sys.exit(1) 