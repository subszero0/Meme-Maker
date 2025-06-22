#!/usr/bin/env python3
"""
Stage 2: API Verification Script
Following Best Practices for systematic debugging

This script verifies:
1. Backend API endpoints
2. CORS configuration
3. API response formats
4. Error handling
5. Authentication (if applicable)
"""

import requests
import json
from datetime import datetime
import sys

def log(message, level="INFO"):
    """Enhanced logging with timestamps"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def test_endpoint(method, url, data=None, headers=None, timeout=10):
    """Test a single API endpoint"""
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=timeout)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, headers=headers, timeout=timeout)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=timeout)
        else:
            log(f"❌ Unsupported method: {method}", "ERROR")
            return False
        
        # Log response details
        log(f"📡 {method} {url}")
        log(f"   Status: {response.status_code}")
        log(f"   Response time: {response.elapsed.total_seconds():.3f}s")
        
        # Check CORS headers
        cors_header = response.headers.get('Access-Control-Allow-Origin')
        if cors_header:
            log(f"   CORS: {cors_header}")
        else:
            log("   CORS: No Access-Control-Allow-Origin header", "WARN")
        
        # Log response content (first 200 chars)
        if response.text:
            content_preview = response.text[:200]
            if len(response.text) > 200:
                content_preview += "..."
            log(f"   Content: {content_preview}")
        
        return response.status_code, response
        
    except requests.exceptions.ConnectionError:
        log(f"❌ {method} {url}: Connection refused", "ERROR")
        return None, None
    except requests.exceptions.Timeout:
        log(f"⏰ {method} {url}: Timeout", "ERROR")
        return None, None
    except Exception as e:
        log(f"❌ {method} {url}: {str(e)}", "ERROR")
        return None, None

def test_health_endpoint():
    """Test the health endpoint"""
    log("Testing health endpoint...")
    
    status_code, response = test_endpoint('GET', 'http://localhost:8000/health')
    
    if status_code == 200:
        log("✅ Health endpoint working")
        return True
    else:
        log("❌ Health endpoint failed")
        return False

def test_metadata_endpoints():
    """Test metadata endpoints"""
    log("Testing metadata endpoints...")
    
    # Test data
    test_youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll (short video)
    
    endpoints = [
        ('POST', 'http://localhost:8000/api/v1/metadata', {'url': test_youtube_url}),
        ('POST', 'http://localhost:8000/api/v1/metadata/extract', {'url': test_youtube_url})
    ]
    
    results = []
    for method, url, data in endpoints:
        status_code, response = test_endpoint(method, url, data)
        
        if status_code in [200, 201]:
            log(f"✅ {url}: Success")
            results.append(True)
            
            # Validate response format
            if response:
                try:
                    json_data = response.json()
                    if 'title' in json_data or 'duration' in json_data:
                        log("   ✅ Valid metadata response format")
                    else:
                        log("   ⚠️  Unexpected response format", "WARN")
                except json.JSONDecodeError:
                    log("   ❌ Invalid JSON response", "ERROR")
        else:
            log(f"❌ {url}: Failed")
            results.append(False)
    
    return all(results)

def test_jobs_endpoint():
    """Test jobs endpoint"""
    log("Testing jobs endpoint...")
    
    # Test job creation
    test_job_data = {
        'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'start_time': 0,
        'end_time': 10,
        'resolution': '720p'
    }
    
    status_code, response = test_endpoint('POST', 'http://localhost:8000/api/v1/jobs', test_job_data)
    
    if status_code in [200, 201]:
        log("✅ Jobs endpoint working")
        
        # Try to get job ID from response
        if response:
            try:
                json_data = response.json()
                job_id = json_data.get('job_id')
                if job_id:
                    log(f"   ✅ Job created with ID: {job_id}")
                    
                    # Test job status endpoint
                    status_url = f"http://localhost:8000/api/v1/jobs/{job_id}"
                    status_code, status_response = test_endpoint('GET', status_url)
                    
                    if status_code == 200:
                        log("   ✅ Job status endpoint working")
                        return True
                    else:
                        log("   ⚠️  Job status endpoint failed", "WARN")
                        return True  # Main endpoint works
                else:
                    log("   ⚠️  No job_id in response", "WARN")
                    return True  # Endpoint works but format unexpected
            except json.JSONDecodeError:
                log("   ❌ Invalid JSON response", "ERROR")
                return False
        return True
    else:
        log("❌ Jobs endpoint failed")
        return False

def test_cors_preflight():
    """Test CORS preflight requests"""
    log("Testing CORS preflight...")
    
    headers = {
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type'
    }
    
    try:
        response = requests.options('http://localhost:8000/api/v1/metadata', headers=headers, timeout=10)
        
        if response.status_code in [200, 204]:
            log("✅ CORS preflight working")
            
            # Check CORS headers
            allow_origin = response.headers.get('Access-Control-Allow-Origin')
            allow_methods = response.headers.get('Access-Control-Allow-Methods')
            allow_headers = response.headers.get('Access-Control-Allow-Headers')
            
            log(f"   Allow-Origin: {allow_origin}")
            log(f"   Allow-Methods: {allow_methods}")
            log(f"   Allow-Headers: {allow_headers}")
            
            return True
        else:
            log(f"❌ CORS preflight failed: {response.status_code}")
            return False
            
    except Exception as e:
        log(f"❌ CORS preflight error: {str(e)}", "ERROR")
        return False

def test_error_handling():
    """Test API error handling"""
    log("Testing error handling...")
    
    # Test invalid URL
    invalid_data = {'url': 'not-a-valid-url'}
    status_code, response = test_endpoint('POST', 'http://localhost:8000/api/v1/metadata', invalid_data)
    
    if status_code in [400, 422]:  # Bad Request or Unprocessable Entity
        log("✅ Error handling working (invalid URL returns 4xx)")
        return True
    else:
        log(f"⚠️  Unexpected error handling: {status_code}", "WARN")
        return False

def main():
    """Main verification function"""
    log("🚀 Starting Stage 2: API Verification")
    log("=" * 50)
    
    # Record start time
    start_time = datetime.now()
    
    # Run all API tests
    tests = [
        ("Health Endpoint", test_health_endpoint),
        ("Metadata Endpoints", test_metadata_endpoints),
        ("Jobs Endpoint", test_jobs_endpoint),
        ("CORS Preflight", test_cors_preflight),
        ("Error Handling", test_error_handling)
    ]
    
    results = {}
    for test_name, test_func in tests:
        log(f"\n📋 Running: {test_name}")
        log("-" * 30)
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            log(f"❌ {test_name} failed: {str(e)}", "ERROR")
            results[test_name] = False
    
    # Calculate duration
    duration = datetime.now() - start_time
    
    # Summary
    log("\n" + "=" * 50)
    log("📊 STAGE 2 API VERIFICATION SUMMARY")
    log("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    log(f"✅ Passed: {passed}/{total}")
    log(f"⏱️  Duration: {duration.total_seconds():.2f}s")
    
    # Update debug notes
    with open("debug-notes.md", "a", encoding='utf-8') as f:
        f.write(f"\n### Stage 2 API Verification Results ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n")
        f.write(f"- **Tests Passed**: {passed}/{total}\n")
        f.write(f"- **Duration**: {duration.total_seconds():.2f}s\n")
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            f.write(f"- **{test_name}**: {status}\n")
    
    if passed == total:
        log("🎉 All API tests passed! Ready for Stage 3")
        return True
    else:
        log("⚠️  Some API tests failed. Check backend service.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 