#!/usr/bin/env python3
"""
Domain and HTTPS Fix Verification Script
Verifies that all fixes have been applied correctly
"""

import requests
import socket
import ssl
import subprocess
import json
import time
from urllib.parse import urlparse

def test_frontend_api_configuration():
    """Test that frontend is using correct API configuration"""
    print("🔍 Testing Frontend API Configuration...")
    
    try:
        # Get the frontend HTML
        response = requests.get("http://13.126.173.223", timeout=10)
        if response.status_code == 200:
            content = response.text
            
            # Check for problematic localhost references
            if 'localhost:8000' in content:
                print("❌ Frontend still references localhost:8000")
                return False
            elif '/api' in content or 'relative' in content.lower():
                print("✅ Frontend using relative API URLs")
                return True
            else:
                print("⚠️  Cannot determine API configuration from HTML")
                return None
        else:
            print(f"❌ Cannot fetch frontend: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
        return False

def test_nginx_configuration():
    """Test Nginx configuration"""
    print("\n🔍 Testing Nginx Configuration...")
    
    # Test HTTP redirect for domain
    try:
        response = requests.get("http://memeit.pro", allow_redirects=False, timeout=10)
        if response.status_code == 301 and 'https' in response.headers.get('Location', ''):
            print("✅ HTTP to HTTPS redirect working")
            return True
        else:
            print(f"❌ HTTP redirect not working: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Nginx redirect test failed: {e}")
        return False

def test_api_routing():
    """Test API routing through Nginx"""
    print("\n🔍 Testing API Routing...")
    
    endpoints = [
        ("http://13.126.173.223/api/health", "IP API Health"),
        ("http://memeit.pro/api/health", "Domain API Health"),
    ]
    
    results = {}
    for url, description in endpoints:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {description}: Working")
                results[url] = True
            else:
                print(f"❌ {description}: HTTP {response.status_code}")
                results[url] = False
        except Exception as e:
            print(f"❌ {description}: {e}")
            results[url] = False
    
    return results

def test_cors_configuration():
    """Test CORS configuration"""
    print("\n🔍 Testing CORS Configuration...")
    
    # Test preflight request
    try:
        response = requests.options(
            "http://13.126.173.223/api/health",
            headers={
                'Origin': 'https://memeit.pro',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            },
            timeout=10
        )
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
        }
        
        if cors_headers['Access-Control-Allow-Origin']:
            print("✅ CORS headers present")
            print(f"   Origin: {cors_headers['Access-Control-Allow-Origin']}")
            return True
        else:
            print("❌ CORS headers missing")
            return False
            
    except Exception as e:
        print(f"❌ CORS test failed: {e}")
        return False

def test_ssl_readiness():
    """Test if SSL certificate paths are configured"""
    print("\n🔍 Testing SSL Readiness...")
    
    # Check if SSL certificate files exist (if running on server)
    ssl_files = [
        "ssl/certs/memeit.pro.crt",
        "ssl/private/memeit.pro.key"
    ]
    
    ssl_ready = True
    for file_path in ssl_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                if 'BEGIN CERTIFICATE' in content or 'BEGIN PRIVATE KEY' in content:
                    print(f"✅ {file_path} exists and valid")
                else:
                    print(f"❌ {file_path} exists but invalid")
                    ssl_ready = False
        except FileNotFoundError:
            print(f"⚠️  {file_path} not found (run setup_ssl_certificate.sh)")
            ssl_ready = False
        except Exception as e:
            print(f"❌ Error checking {file_path}: {e}")
            ssl_ready = False
    
    return ssl_ready

def test_docker_configuration():
    """Test Docker configuration"""
    print("\n🔍 Testing Docker Configuration...")
    
    try:
        # Check if containers are running
        result = subprocess.run(['docker-compose', 'ps'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            output = result.stdout
            if 'meme-maker-frontend' in output and 'Up' in output:
                print("✅ Frontend container running")
                
                # Check port mappings
                if '80:80' in output and '443:443' in output:
                    print("✅ Correct port mappings (80:80, 443:443)")
                    return True
                else:
                    print("❌ Incorrect port mappings")
                    return False
            else:
                print("❌ Frontend container not running")
                return False
        else:
            print("❌ Docker Compose not accessible")
            return False
            
    except Exception as e:
        print(f"❌ Docker test failed: {e}")
        return False

def test_end_to_end_flow():
    """Test complete end-to-end flow"""
    print("\n🔍 Testing End-to-End Flow...")
    
    try:
        # Test video metadata API
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        response = requests.post(
            "http://13.126.173.223/api/v1/metadata",
            json={"url": test_url},
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'title' in data and 'duration' in data:
                print(f"✅ End-to-end API working: {data['title'][:50]}...")
                return True
            else:
                print("❌ API response missing required fields")
                return False
        else:
            print(f"❌ API returned HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ End-to-end test failed: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🔍 DOMAIN AND HTTPS FIX VERIFICATION")
    print("====================================")
    
    # Run all tests
    tests = [
        ("Frontend API Configuration", test_frontend_api_configuration),
        ("Nginx Configuration", test_nginx_configuration),
        ("API Routing", test_api_routing),
        ("CORS Configuration", test_cors_configuration),
        ("SSL Readiness", test_ssl_readiness),
        ("Docker Configuration", test_docker_configuration),
        ("End-to-End Flow", test_end_to_end_flow),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    warnings = sum(1 for r in results.values() if r is None)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⚠️  WARNING"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Results: {passed} passed, {failed} failed, {warnings} warnings")
    
    # Recommendations
    print("\n📋 NEXT STEPS:")
    
    if failed == 0:
        print("🎉 All tests passed! Your domain and HTTPS fixes are working.")
        if warnings > 0:
            print("⚠️  Some warnings detected - SSL certificates may need setup.")
            print("   Run: sudo ./setup_ssl_certificate.sh")
    else:
        print("❌ Some tests failed. Check the output above and fix issues.")
        
        if not results.get("Docker Configuration"):
            print("1. Restart Docker services: docker-compose up -d")
        
        if not results.get("SSL Readiness"):
            print("2. Set up SSL certificates: sudo ./setup_ssl_certificate.sh")
        
        if not results.get("API Routing"):
            print("3. Check backend service: docker-compose logs backend")
    
    print("\n🔗 Test URLs:")
    print("   HTTP (IP):     http://13.126.173.223")
    print("   HTTP (Domain): http://memeit.pro")
    print("   HTTPS:         https://memeit.pro (after SSL setup)")

if __name__ == "__main__":
    main() 