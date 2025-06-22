#!/usr/bin/env python3
"""
Stage 1: System Verification Script
Following Best Practices for systematic debugging

This script verifies:
1. Docker services status
2. Network connectivity
3. Port availability  
4. Environment variables
5. Basic system health
"""

import subprocess
import sys
import requests
import json
from datetime import datetime
import os
from pathlib import Path

def log(message, level="INFO"):
    """Enhanced logging with timestamps"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def run_command(cmd, check=False):
    """Run command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def check_docker_status():
    """Check Docker Desktop and container status"""
    log("Checking Docker status...")
    
    # Check if Docker is running
    returncode, stdout, stderr = run_command("docker --version")
    if returncode != 0:
        log("❌ Docker not found or not running", "ERROR")
        return False
    
    log(f"✅ Docker version: {stdout.strip()}")
    
    # Check Docker Desktop status  
    returncode, stdout, stderr = run_command("docker ps")
    if returncode != 0:
        log("❌ Docker Desktop not running", "ERROR")
        log(f"Error: {stderr}", "ERROR")
        return False
    
    log("✅ Docker Desktop is running")
    
    # Check containers
    if stdout.strip():
        log("📋 Running containers:")
        for line in stdout.split('\n')[1:]:  # Skip header
            if line.strip():
                log(f"  {line}")
    else:
        log("⚠️  No containers currently running", "WARN")
    
    return True

def check_ports():
    """Check if required ports are available/in use"""
    log("Checking port status...")
    
    ports_to_check = [3000, 8000, 8080, 6379, 5432]
    
    for port in ports_to_check:
        returncode, stdout, stderr = run_command(f"netstat -an | findstr :{port}")
        if returncode == 0 and stdout.strip():
            log(f"🔗 Port {port}: IN USE")
        else:
            log(f"⭕ Port {port}: AVAILABLE")

def check_environment():
    """Check environment variables and configuration"""
    log("Checking environment configuration...")
    
    # Check for .env files
    env_files = ['.env', '.env.local', '.env.production']
    for env_file in env_files:
        if os.path.exists(env_file):
            log(f"✅ Found {env_file}")
        else:
            log(f"❌ Missing {env_file}")
    
    # Check key environment variables
    key_vars = ['DOCKER_IMAGE_TAG', 'BACKEND_URL', 'FRONTEND_URL']
    for var in key_vars:
        value = os.getenv(var)
        if value:
            log(f"✅ {var}={value}")
        else:
            log(f"⚠️  {var} not set")

def check_network_connectivity():
    """Test basic network connectivity"""
    log("Checking network connectivity...")
    
    # Test localhost connectivity
    test_urls = [
        "http://localhost:3000",
        "http://localhost:8000", 
        "http://localhost:8000/health"
    ]
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=5)
            log(f"✅ {url}: {response.status_code}")
        except requests.exceptions.ConnectionError:
            log(f"❌ {url}: Connection refused")
        except requests.exceptions.Timeout:
            log(f"⚠️  {url}: Timeout")
        except Exception as e:
            log(f"❌ {url}: {str(e)}")

def check_file_structure():
    """Verify critical files exist"""
    log("Checking file structure...")
    
    critical_files = [
        'docker-compose.yaml',
        'docker-compose.dev.yaml',
        'frontend-new/package.json',
        'backend/app/main.py',
        'worker/main.py',
        'start_development.py'
    ]
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            log(f"✅ {file_path}")
        else:
            log(f"❌ Missing {file_path}")

def main():
    """Main verification function"""
    log("🚀 Starting Stage 1: System Verification")
    log("=" * 50)
    
    # Save current commit hash for rollback safety
    returncode, stdout, stderr = run_command("git rev-parse HEAD")
    if returncode == 0:
        commit_hash = stdout.strip()
        log(f"📝 Current commit: {commit_hash}")
        
        # Save to debug notes
        with open("debug-notes.md", "a", encoding='utf-8') as f:
            f.write(f"\n### Stage 1 Verification Results ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n")
            f.write(f"- **Commit Hash**: `{commit_hash}`\n")
    
    # Run all checks
    checks = [
        ("Docker Status", check_docker_status),
        ("Port Status", check_ports),
        ("Environment", check_environment), 
        ("Network Connectivity", check_network_connectivity),
        ("File Structure", check_file_structure)
    ]
    
    results = {}
    for check_name, check_func in checks:
        log(f"\n📋 Running: {check_name}")
        log("-" * 30)
        try:
            result = check_func()
            results[check_name] = result
        except Exception as e:
            log(f"❌ {check_name} failed: {str(e)}", "ERROR")
            results[check_name] = False
    
    # Summary
    log("\n" + "=" * 50)
    log("📊 STAGE 1 VERIFICATION SUMMARY")
    log("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    log(f"✅ Passed: {passed}/{total}")
    
    if passed == total:
        log("🎉 All checks passed! Ready for Stage 2")
        return True
    else:
        log("⚠️  Some checks failed. Address issues before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 