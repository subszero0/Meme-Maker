#!/usr/bin/env python3
"""
Fix Pre-HTTPS Issues Script
Addresses issues found in Stage 1 verification
"""

import subprocess
import requests
import time
import yaml

def fix_docker_port_mapping():
    """Fix Docker port mapping issues"""
    print("🔧 Checking Docker Compose configuration...")
    
    try:
        # Read current docker-compose.yaml
        with open('docker-compose.yaml', 'r') as f:
            content = f.read()
        
        # Check if 443:443 mapping exists
        if '443:443' in content:
            print("✅ Port 443 mapping already configured")
            return True
        else:
            print("❌ Port 443 mapping missing")
            return False
            
    except Exception as e:
        print(f"❌ Error checking docker-compose.yaml: {e}")
        return False

def check_backend_api_routes():
    """Check if backend API routes are working"""
    print("🔧 Testing backend API routes directly...")
    
    try:
        # Test backend health endpoint directly
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            print("✅ Backend health endpoint working")
        else:
            print(f"❌ Backend health endpoint failed: {response.status_code}")
            return False
            
        # Test backend API routes
        try:
            response = requests.get("http://localhost:8000/api/health", timeout=10)
            if response.status_code == 200:
                print("✅ Backend API health endpoint working")
                return True
            else:
                print(f"⚠️ Backend API endpoint returns {response.status_code}")
                
                # Check if it's a 404 - might need route fix
                if response.status_code == 404:
                    print("💡 Backend API routes might need checking")
                return False
        except Exception as e:
            print(f"❌ Backend API test failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        return False

def restart_containers():
    """Restart containers to apply any fixes"""
    print("🔄 Restarting containers...")
    
    try:
        # Stop containers
        subprocess.run(['docker-compose', 'down'], check=True)
        time.sleep(5)
        
        # Start containers
        subprocess.run(['docker-compose', 'up', '-d'], check=True)
        time.sleep(30)
        
        # Check status
        result = subprocess.run(['docker-compose', 'ps'], 
                              capture_output=True, text=True)
        print("📊 Container status:")
        print(result.stdout)
        
        return True
        
    except Exception as e:
        print(f"❌ Container restart failed: {e}")
        return False

def fix_nginx_port_mapping():
    """Ensure nginx is listening on correct ports"""
    print("🔧 Checking nginx port configuration...")
    
    try:
        # Check if nginx is listening on port 80 inside container
        result = subprocess.run([
            'docker-compose', 'exec', '-T', 'frontend', 
            'netstat', '-tlnp'
        ], capture_output=True, text=True, timeout=10)
        
        if ':80' in result.stdout:
            print("✅ Nginx listening on port 80")
        else:
            print("❌ Nginx not listening on port 80")
            return False
            
        return True
        
    except Exception as e:
        print(f"⚠️ Could not check nginx ports: {e}")
        return True  # Don't fail for this check

def test_api_routing():
    """Test API routing through nginx"""
    print("🔧 Testing API routing through nginx...")
    
    endpoints_to_test = [
        ("http://localhost/api/health", "Local API"),
        ("http://13.126.173.223/api/health", "IP API"),
    ]
    
    for url, description in endpoints_to_test:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {description}: Working")
            else:
                print(f"❌ {description}: HTTP {response.status_code}")
                
                # If it's 404, might be nginx config issue
                if response.status_code == 404:
                    print(f"💡 {description}: Check nginx API proxy configuration")
                    
        except Exception as e:
            print(f"❌ {description}: {e}")

def check_firewall():
    """Check firewall settings for port 443"""
    print("🔧 Checking firewall settings...")
    
    try:
        result = subprocess.run(['sudo', 'ufw', 'status'], 
                              capture_output=True, text=True, timeout=10)
        
        if 'Status: active' in result.stdout:
            print("🔥 UFW firewall is active")
            if '443' in result.stdout:
                print("✅ Port 443 allowed in firewall")
            else:
                print("⚠️ Port 443 not explicitly allowed")
                print("💡 Run: sudo ufw allow 443")
        else:
            print("✅ UFW firewall is inactive")
            
    except Exception as e:
        print(f"⚠️ Could not check firewall: {e}")

def main():
    """Run all fixes"""
    print("🔧 PRE-HTTPS ISSUES FIX")
    print("========================")
    
    fixes = [
        ("Docker Port Mapping", fix_docker_port_mapping),
        ("Backend API Routes", check_backend_api_routes),
        ("Nginx Port Mapping", fix_nginx_port_mapping),
    ]
    
    need_restart = False
    
    for fix_name, fix_func in fixes:
        print(f"\n🔍 {fix_name}...")
        result = fix_func()
        if not result:
            need_restart = True
    
    # Test API routing
    print(f"\n🔍 API Routing...")
    test_api_routing()
    
    # Check firewall
    print(f"\n🔍 Firewall...")
    check_firewall()
    
    # Restart if needed
    if need_restart:
        print(f"\n🔄 Some issues found, restarting containers...")
        restart_containers()
        
        # Re-test after restart
        print(f"\n🧪 Re-testing after restart...")
        time.sleep(10)
        test_api_routing()
    
    print("\n" + "="*50)
    print("🎯 SUMMARY & NEXT STEPS")
    print("="*50)
    print("1. If API routing still fails, check backend logs:")
    print("   docker-compose logs backend")
    print("")
    print("2. If port 443 issues persist, allow in firewall:")
    print("   sudo ufw allow 443")
    print("")
    print("3. After fixing issues, re-run HTTPS setup:")
    print("   python3 complete_https_setup.py")
    print("")
    print("4. To debug nginx routing:")
    print("   docker-compose logs frontend")

if __name__ == "__main__":
    main() 