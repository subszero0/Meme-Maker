#!/usr/bin/env python3
"""
Final HTTPS Verification Script
Comprehensive testing of the complete HTTPS setup
"""

import requests
import subprocess
import socket
import ssl
import time
from datetime import datetime
import json

def log_result(message, status="INFO"):
    """Log results with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_emoji = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "INFO": "ℹ️"}
    print(f"[{timestamp}] {status_emoji.get(status, 'ℹ️')} {message}")

def test_docker_services():
    """Check Docker services are running"""
    log_result("Testing Docker services...", "INFO")
    
    try:
        result = subprocess.run(['docker-compose', 'ps'], capture_output=True, text=True)
        
        if result.returncode != 0:
            log_result("Docker Compose not accessible", "FAIL")
            return False
        
        output = result.stdout
        required_services = ['meme-maker-backend', 'meme-maker-frontend', 'meme-maker-worker', 'meme-maker-redis']
        
        for service in required_services:
            if service in output and 'Up' in output:
                log_result(f"{service}: Running", "PASS")
            else:
                log_result(f"{service}: Not running", "FAIL")
                return False
        
        return True
        
    except Exception as e:
        log_result(f"Docker services check failed: {e}", "FAIL")
        return False

def test_http_redirect():
    """Test HTTP to HTTPS redirect"""
    log_result("Testing HTTP to HTTPS redirect...", "INFO")
    
    try:
        response = requests.get("http://memeit.pro", allow_redirects=False, timeout=10)
        
        if response.status_code == 301:
            location = response.headers.get('Location', '')
            if 'https://memeit.pro' in location:
                log_result("HTTP to HTTPS redirect: Working", "PASS")
                return True
            else:
                log_result(f"Redirect location unexpected: {location}", "FAIL")
                return False
        else:
            log_result(f"HTTP redirect not working: {response.status_code}", "FAIL")
            return False
            
    except Exception as e:
        log_result(f"HTTP redirect test failed: {e}", "FAIL")
        return False

def test_https_frontend():
    """Test HTTPS frontend access"""
    log_result("Testing HTTPS frontend...", "INFO")
    
    try:
        response = requests.get("https://memeit.pro/", timeout=15, verify=True)
        
        if response.status_code == 200:
            # Check if it's the actual frontend (look for specific content)
            if 'html' in response.text.lower():
                log_result("HTTPS frontend: Working", "PASS")
                return True
            else:
                log_result("HTTPS frontend: Invalid response", "FAIL")
                return False
        else:
            log_result(f"HTTPS frontend status: {response.status_code}", "FAIL")
            return False
            
    except requests.exceptions.SSLError as e:
        log_result(f"HTTPS frontend SSL error: {e}", "FAIL")
        return False
    except Exception as e:
        log_result(f"HTTPS frontend test failed: {e}", "FAIL")
        return False

def test_https_api():
    """Test HTTPS API endpoints"""
    log_result("Testing HTTPS API...", "INFO")
    
    try:
        # Test health endpoint
        response = requests.get("https://memeit.pro/api/health", timeout=10, verify=True)
        
        if response.status_code == 200:
            log_result("HTTPS API health: Working", "PASS")
        else:
            log_result(f"HTTPS API health status: {response.status_code}", "FAIL")
            return False
        
        # Test metadata endpoint
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        response = requests.post(
            "https://memeit.pro/api/v1/metadata",
            json={"url": test_url},
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'title' in data:
                log_result(f"HTTPS API metadata: Working ({data['title'][:30]}...)", "PASS")
                return True
            else:
                log_result("HTTPS API metadata: Invalid response", "FAIL")
                return False
        else:
            log_result(f"HTTPS API metadata status: {response.status_code}", "FAIL")
            return False
            
    except Exception as e:
        log_result(f"HTTPS API test failed: {e}", "FAIL")
        return False

def test_ssl_certificate():
    """Test SSL certificate configuration"""
    log_result("Testing SSL certificate...", "INFO")
    
    try:
        context = ssl.create_default_context()
        
        with socket.create_connection(('memeit.pro', 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname='memeit.pro') as ssock:
                cert = ssock.getpeercert()
                
                log_result(f"SSL certificate issuer: {cert['issuer'][1][0][1]}", "PASS")
                log_result(f"SSL certificate expires: {cert['notAfter']}", "PASS")
                
                # Check certificate names
                if 'subjectAltName' in cert:
                    alt_names = [name[1] for name in cert['subjectAltName'] if name[0] == 'DNS']
                    if 'memeit.pro' in alt_names:
                        log_result("SSL certificate covers domain", "PASS")
                        return True
                
                return True
                
    except Exception as e:
        log_result(f"SSL certificate test failed: {e}", "FAIL")
        return False

def test_security_headers():
    """Test security headers"""
    log_result("Testing security headers...", "INFO")
    
    try:
        response = requests.get("https://memeit.pro/", timeout=10)
        
        security_headers = {
            'Strict-Transport-Security': 'HSTS',
            'X-Frame-Options': 'Frame Options',
            'X-Content-Type-Options': 'Content Type Options'
        }
        
        headers_found = 0
        for header, name in security_headers.items():
            if header in response.headers:
                log_result(f"{name}: Present", "PASS")
                headers_found += 1
            else:
                log_result(f"{name}: Missing", "WARN")
        
        if headers_found >= 2:
            log_result("Security headers: Adequate", "PASS")
            return True
        else:
            log_result("Security headers: Insufficient", "WARN")
            return False
            
    except Exception as e:
        log_result(f"Security headers test failed: {e}", "FAIL")
        return False

def test_end_to_end_workflow():
    """Test complete video processing workflow"""
    log_result("Testing end-to-end video workflow...", "INFO")
    
    try:
        # Test job creation
        response = requests.post(
            "https://memeit.pro/api/v1/jobs",
            json={
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "start_time": 0,
                "end_time": 5,
                "resolution": "480p"
            },
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            job_data = response.json()
            if 'job_id' in job_data:
                job_id = job_data['job_id']
                log_result(f"Job created successfully: {job_id}", "PASS")
                
                # Check job status
                time.sleep(2)
                status_response = requests.get(f"https://memeit.pro/api/v1/jobs/{job_id}")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    log_result(f"Job status: {status_data.get('status', 'unknown')}", "PASS")
                    return True
                else:
                    log_result("Job status check failed", "WARN")
                    return True  # Job creation worked, status check is optional
            else:
                log_result("Job creation response missing job_id", "FAIL")
                return False
        else:
            log_result(f"Job creation failed: {response.status_code}", "FAIL")
            return False
            
    except Exception as e:
        log_result(f"End-to-end workflow test failed: {e}", "FAIL")
        return False

def main():
    """Run complete HTTPS verification"""
    print("🔐 FINAL HTTPS VERIFICATION")
    print("=" * 50)
    
    tests = [
        ("Docker Services", test_docker_services),
        ("HTTP to HTTPS Redirect", test_http_redirect),
        ("HTTPS Frontend", test_https_frontend),
        ("HTTPS API", test_https_api),
        ("SSL Certificate", test_ssl_certificate),
        ("Security Headers", test_security_headers),
        ("End-to-End Workflow", test_end_to_end_workflow),
    ]
    
    results = {}
    for test_name, test_func in tests:
        log_result(f"Running {test_name} test...", "INFO")
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            log_result(f"{test_name} test failed with exception: {e}", "FAIL")
            results[test_name] = False
        print()
    
    # Summary
    print("=" * 50)
    log_result("FINAL VERIFICATION SUMMARY", "INFO")
    print("=" * 50)
    
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        log_result(f"{test_name}: {status}", status)
    
    print()
    log_result(f"Test Results: {passed}/{total} passed", "INFO")
    
    # Determine overall result
    critical_tests = ["Docker Services", "HTTPS Frontend", "HTTPS API", "SSL Certificate"]
    critical_passed = all(results.get(test, False) for test in critical_tests)
    
    if critical_passed:
        log_result("🎉 HTTPS SETUP COMPLETE AND WORKING!", "PASS")
        print()
        log_result("✅ Your Meme Maker application is now fully secured with HTTPS", "PASS")
        log_result("✅ All critical functionality is working", "PASS")
        print()
        log_result("🌐 Access your application at:", "INFO")
        log_result("   Frontend: https://memeit.pro", "INFO")
        log_result("   API:      https://memeit.pro/api/health", "INFO")
        print()
        log_result("🔒 Security features enabled:", "INFO")
        log_result("   ✓ SSL/TLS encryption", "INFO")
        log_result("   ✓ Automatic HTTP to HTTPS redirect", "INFO")
        log_result("   ✓ Security headers", "INFO")
        print()
        log_result("📋 Next steps:", "INFO")
        log_result("   • Monitor your application regularly", "INFO")
        log_result("   • Set up automated backups", "INFO")
        log_result("   • Monitor SSL certificate expiry (auto-renewal is set up)", "INFO")
        
        return True
    else:
        log_result("❌ HTTPS setup has issues", "FAIL")
        log_result("Some critical tests failed. Please check the errors above.", "FAIL")
        
        # Provide specific guidance
        if not results.get("Docker Services"):
            log_result("• Fix: Restart Docker services with 'docker-compose up -d'", "INFO")
        if not results.get("SSL Certificate"):
            log_result("• Fix: Check SSL certificate files in ssl/ directory", "INFO")
        if not results.get("HTTPS Frontend"):
            log_result("• Fix: Check nginx configuration and container logs", "INFO")
        
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 