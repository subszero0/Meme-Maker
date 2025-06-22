#!/usr/bin/env python3
"""
Stage 1: Pre-HTTPS Setup Verification
Verifies the current HTTP setup is working before SSL installation
"""

import requests
import subprocess
import socket
import time
import json
from datetime import datetime

def log_result(message, status="INFO"):
    """Log results with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_emoji = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "INFO": "ℹ️"}
    print(f"[{timestamp}] {status_emoji.get(status, 'ℹ️')} {message}")

def test_docker_services():
    """Verify all Docker services are running"""
    log_result("Testing Docker Services...", "INFO")
    
    try:
        # Check docker-compose services
        result = subprocess.run(['docker-compose', 'ps'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            log_result("Docker Compose not accessible", "FAIL")
            return False
        
        output = result.stdout
        required_services = ['meme-maker-backend', 'meme-maker-frontend', 'meme-maker-worker', 'meme-maker-redis']
        
        for service in required_services:
            if service in output and 'Up' in output:
                log_result(f"{service}: Running", "PASS")
            else:
                log_result(f"{service}: Not running or unhealthy", "FAIL")
                return False
        
        # Check port mappings
        if '80:80' in output:
            log_result("Port 80 mapping: Correct", "PASS")
        else:
            log_result("Port 80 mapping: Missing or incorrect", "FAIL")
            return False
            
        if '443:443' in output:
            log_result("Port 443 mapping: Already configured", "PASS")
        else:
            log_result("Port 443 mapping: Not configured (will be added)", "WARN")
        
        return True
        
    except Exception as e:
        log_result(f"Docker services check failed: {e}", "FAIL")
        return False

def test_http_endpoints():
    """Test HTTP endpoints are working"""
    log_result("Testing HTTP Endpoints...", "INFO")
    
    endpoints = [
        ("http://localhost/", "Local frontend"),
        ("http://13.126.173.223/", "IP frontend"),
        ("http://memeit.pro/", "Domain frontend"),
        ("http://localhost:8000/health", "Backend health"),
        ("http://13.126.173.223/api/health", "API via IP"),
        ("http://memeit.pro/api/health", "API via domain")
    ]
    
    all_pass = True
    for url, description in endpoints:
        try:
            response = requests.get(url, timeout=10, allow_redirects=False)
            if response.status_code == 200:
                log_result(f"{description}: Working (200)", "PASS")
            elif response.status_code == 301 and 'https' in response.headers.get('Location', ''):
                log_result(f"{description}: HTTPS redirect working (301)", "PASS")
            else:
                log_result(f"{description}: Unexpected status {response.status_code}", "WARN")
                all_pass = False
        except Exception as e:
            log_result(f"{description}: Failed - {e}", "FAIL")
            all_pass = False
    
    return all_pass

def test_ssl_directory_setup():
    """Check if SSL directories exist or can be created"""
    log_result("Checking SSL Directory Setup...", "INFO")
    
    import os
    
    directories = ['ssl/certs', 'ssl/private']
    for directory in directories:
        if os.path.exists(directory):
            log_result(f"{directory}: Exists", "PASS")
        else:
            try:
                os.makedirs(directory, exist_ok=True)
                log_result(f"{directory}: Created", "PASS")
            except Exception as e:
                log_result(f"{directory}: Cannot create - {e}", "FAIL")
                return False
    
    return True

def test_domain_dns():
    """Test domain DNS resolution"""
    log_result("Testing Domain DNS Resolution...", "INFO")
    
    try:
        ip = socket.gethostbyname('memeit.pro')
        log_result(f"memeit.pro resolves to: {ip}", "PASS")
        
        # Check if it resolves to the expected IP
        if ip == "13.126.173.223":
            log_result("DNS points to correct server IP", "PASS")
            return True
        else:
            log_result(f"DNS points to {ip}, expected 13.126.173.223", "WARN")
            return True  # Still allow HTTPS setup
    except Exception as e:
        log_result(f"DNS resolution failed: {e}", "FAIL")
        return False

def test_ports_open():
    """Test if required ports are open"""
    log_result("Testing Port Accessibility...", "INFO")
    
    ports = [80, 443, 8000]
    
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        try:
            result = sock.connect_ex(('localhost', port))
            if result == 0:
                log_result(f"Port {port}: Open", "PASS")
            else:
                log_result(f"Port {port}: Closed or filtered", "FAIL" if port != 443 else "WARN")
        except Exception as e:
            log_result(f"Port {port} test failed: {e}", "FAIL")
        finally:
            sock.close()

def check_certbot_requirements():
    """Check if certbot can be installed"""
    log_result("Checking Certbot Requirements...", "INFO")
    
    # Check if snap is available
    try:
        result = subprocess.run(['which', 'snap'], capture_output=True, text=True)
        if result.returncode == 0:
            log_result("Snap package manager: Available", "PASS")
        else:
            log_result("Snap package manager: Not found (will be installed)", "WARN")
    except Exception:
        log_result("Cannot check snap availability", "WARN")
    
    # Check if certbot is already installed
    try:
        result = subprocess.run(['which', 'certbot'], capture_output=True, text=True)
        if result.returncode == 0:
            log_result("Certbot: Already installed", "PASS")
        else:
            log_result("Certbot: Not installed (will be installed)", "INFO")
    except Exception:
        log_result("Cannot check certbot", "INFO")

def main():
    """Run all pre-HTTPS verification tests"""
    print("🔍 STAGE 1: PRE-HTTPS SETUP VERIFICATION")
    print("=" * 50)
    
    tests = [
        ("Docker Services", test_docker_services),
        ("HTTP Endpoints", test_http_endpoints),
        ("SSL Directory Setup", test_ssl_directory_setup),
        ("Domain DNS", test_domain_dns),
        ("Port Accessibility", test_ports_open),
        ("Certbot Requirements", check_certbot_requirements),
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
        print()  # Add spacing between tests
    
    # Summary
    print("=" * 50)
    log_result("STAGE 1 VERIFICATION SUMMARY", "INFO")
    print("=" * 50)
    
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        log_result(f"{test_name}: {status}", status)
    
    print()
    log_result(f"Results: {passed} passed, {failed} failed", "INFO")
    
    if failed == 0:
        log_result("✅ All pre-checks passed! Ready for Stage 2: SSL Certificate Installation", "PASS")
        log_result("Next: Run 'python stage2_ssl_installation.py'", "INFO")
        return True
    else:
        log_result("❌ Some pre-checks failed. Fix issues before proceeding with SSL setup.", "FAIL")
        log_result("Fix the failed tests and run this script again.", "INFO")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 