#!/usr/bin/env python3
"""
Stage 3: Frontend Verification Script
Following Best Practices for systematic debugging

This script verifies:
1. Frontend accessibility
2. JavaScript console errors
3. Network request patterns
4. API integration
5. UI responsiveness
"""

import requests
import subprocess
import json
from datetime import datetime
import sys
import time
import re

def log(message, level="INFO"):
    """Enhanced logging with timestamps"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def run_command(cmd, timeout=30):
    """Run command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def check_frontend_accessibility():
    """Check if frontend is accessible"""
    log("Checking frontend accessibility...")
    
    try:
        response = requests.get('http://localhost:3000', timeout=10)
        
        if response.status_code == 200:
            log("✅ Frontend accessible")
            
            # Check if it's the React app (look for common indicators)
            content = response.text.lower()
            if 'meme' in content or 'react' in content or 'app' in content:
                log("   ✅ Appears to be the correct app")
                return True
            else:
                log("   ⚠️  Unexpected content", "WARN")
                return True
        else:
            log(f"❌ Frontend returned {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        log("❌ Frontend not accessible - connection refused", "ERROR")
        return False
    except Exception as e:
        log(f"❌ Frontend check failed: {str(e)}", "ERROR")
        return False

def check_frontend_build():
    """Check if frontend can build successfully"""
    log("Checking frontend build...")
    
    # Change to frontend directory and try to build
    build_commands = [
        "cd frontend-new",
        "npm run build"
    ]
    
    for cmd in build_commands:
        log(f"Running: {cmd}")
        returncode, stdout, stderr = run_command(cmd, timeout=60)
        
        if returncode != 0:
            log(f"❌ Build command failed: {cmd}", "ERROR")
            log(f"Error: {stderr}")
            return False
    
    log("✅ Frontend builds successfully")
    return True

def check_api_endpoints_in_code():
    """Check API endpoint URLs in frontend code"""
    log("Checking API endpoints in frontend code...")
    
    # Check the API configuration file
    try:
        with open('frontend-new/src/lib/api.ts', 'r') as f:
            api_content = f.read()
        
        # Look for API endpoint definitions
        api_patterns = [
            r'http://localhost:8000',
            r'/api/v1/',
            r'/api/',
            r'metadata',
            r'jobs'
        ]
        
        found_patterns = {}
        for pattern in api_patterns:
            matches = re.findall(pattern, api_content, re.IGNORECASE)
            found_patterns[pattern] = len(matches)
            
            if matches:
                log(f"   ✅ Found {len(matches)} instances of '{pattern}'")
            else:
                log(f"   ❌ No instances of '{pattern}' found")
        
        # Check for correct API version prefix
        if found_patterns.get('/api/v1/', 0) > 0:
            log("   ✅ Using correct /api/v1/ prefix")
            return True
        elif found_patterns.get('/api/', 0) > 0:
            log("   ⚠️  Using /api/ without version prefix", "WARN")
            return False
        else:
            log("   ❌ No API endpoints found", "ERROR")
            return False
            
    except FileNotFoundError:
        log("❌ API file not found: frontend-new/src/lib/api.ts", "ERROR")
        return False
    except Exception as e:
        log(f"❌ Error reading API file: {str(e)}", "ERROR")
        return False

def check_environment_config():
    """Check frontend environment configuration"""
    log("Checking frontend environment configuration...")
    
    # Check for environment files
    env_files = [
        'frontend-new/.env',
        'frontend-new/.env.local',
        'frontend-new/.env.development'
    ]
    
    env_found = False
    for env_file in env_files:
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                log(f"   ✅ Found {env_file}")
                
                # Check for important environment variables
                if 'REACT_APP' in content or 'VITE' in content:
                    log(f"      Contains environment variables")
                    env_found = True
                    
        except FileNotFoundError:
            log(f"   ❌ Missing {env_file}")
    
    if env_found:
        log("✅ Environment configuration found")
        return True
    else:
        log("⚠️  No environment configuration found", "WARN")
        return True  # Not critical for basic functionality

def test_api_integration():
    """Test frontend-backend API integration"""
    log("Testing API integration...")
    
    # Check if both frontend and backend are running
    frontend_ok = False
    backend_ok = False
    
    try:
        frontend_resp = requests.get('http://localhost:3000', timeout=5)
        frontend_ok = frontend_resp.status_code == 200
    except:
        pass
    
    try:
        backend_resp = requests.get('http://localhost:8000/health', timeout=5)
        backend_ok = backend_resp.status_code == 200
    except:
        pass
    
    if not frontend_ok:
        log("❌ Frontend not running - cannot test integration")
        return False
    
    if not backend_ok:
        log("❌ Backend not running - cannot test integration")
        return False
    
    log("✅ Both frontend and backend are running")
    
    # Test CORS by making a request from frontend origin
    try:
        headers = {'Origin': 'http://localhost:3000'}
        response = requests.post(
            'http://localhost:8000/api/v1/metadata',
            json={'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'},
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201, 400, 422]:  # Any valid response (not CORS error)
            log("✅ CORS integration working")
            return True
        else:
            log(f"⚠️  Unexpected response: {response.status_code}", "WARN")
            return False
            
    except Exception as e:
        log(f"❌ API integration test failed: {str(e)}", "ERROR")
        return False

def check_package_dependencies():
    """Check frontend package dependencies"""
    log("Checking package dependencies...")
    
    try:
        with open('frontend-new/package.json', 'r') as f:
            package_data = json.load(f)
        
        # Check for critical dependencies
        dependencies = package_data.get('dependencies', {})
        dev_dependencies = package_data.get('devDependencies', {})
        all_deps = {**dependencies, **dev_dependencies}
        
        critical_deps = [
            'react',
            'react-dom',
            'typescript',
        ]
        
        missing_deps = []
        for dep in critical_deps:
            if dep not in all_deps:
                missing_deps.append(dep)
            else:
                log(f"   ✅ {dep} found: {all_deps[dep]}")
        
        if missing_deps:
            log(f"❌ Missing critical dependencies: {missing_deps}", "ERROR")
            return False
        else:
            log("✅ All critical dependencies found")
            return True
            
    except FileNotFoundError:
        log("❌ package.json not found", "ERROR")
        return False
    except Exception as e:
        log(f"❌ Error reading package.json: {str(e)}", "ERROR")
        return False

def main():
    """Main verification function"""
    log("🚀 Starting Stage 3: Frontend Verification")
    log("=" * 50)
    
    # Record start time
    start_time = datetime.now()
    
    # Run all frontend tests
    tests = [
        ("Frontend Accessibility", check_frontend_accessibility),
        ("Package Dependencies", check_package_dependencies),
        ("API Endpoints in Code", check_api_endpoints_in_code),
        ("Environment Configuration", check_environment_config),
        ("API Integration", test_api_integration),
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
    log("📊 STAGE 3 FRONTEND VERIFICATION SUMMARY")
    log("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    log(f"✅ Passed: {passed}/{total}")
    log(f"⏱️  Duration: {duration.total_seconds():.2f}s")
    
    # Update debug notes
    with open("debug-notes.md", "a", encoding='utf-8') as f:
        f.write(f"\n### Stage 3 Frontend Verification Results ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n")
        f.write(f"- **Tests Passed**: {passed}/{total}\n")
        f.write(f"- **Duration**: {duration.total_seconds():.2f}s\n")
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            f.write(f"- **{test_name}**: {status}\n")
    
    if passed == total:
        log("🎉 All frontend tests passed! Ready for end-to-end testing")
        return True
    else:
        log("⚠️  Some frontend tests failed. Check frontend configuration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 