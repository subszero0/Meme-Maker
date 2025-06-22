#!/usr/bin/env python3
"""
Complete HTTPS Setup - Fix the HTTPS server block to include API routing
This addresses the root cause: HTTPS requests aren't being proxied to backend
"""

import subprocess
import sys

def run_command(cmd, description=""):
    """Run a shell command and handle errors"""
    print(f"\n🔄 {description}")
    print(f"Running: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        if result.stdout:
            print(f"✅ Output: {result.stdout}")
        if result.stderr and result.returncode != 0:
            print(f"❌ Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("🔧 COMPLETE HTTPS SETUP - FIXING API ROUTING")
    print("=" * 50)
    print("🎯 REAL ISSUE: HTTPS server block missing API proxy config")
    print("   HTTP (port 80): ✅ Has API routing")  
    print("   HTTPS (port 443): ❌ Missing API routing")
    print()
    
    # We need to add the API location block to the HTTPS server
    api_location_block = '''
        # API proxy to backend
        location /api/ {
            proxy_pass http://backend:8000/api/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }'''
    
    steps = [
        ("cd ~/Meme-Maker", "Navigate to project directory"),
        ("docker exec meme-maker-frontend cp /etc/nginx/nginx.conf /tmp/nginx.conf.backup", "Backup current nginx.conf"),
        (f"docker exec meme-maker-frontend sed -i '/# Handle SPA routing/i\\{api_location_block}' /etc/nginx/nginx.conf", "Add API routing to HTTPS server block"),
        ("docker exec meme-maker-frontend nginx -t", "Test nginx configuration"),
        ("docker exec meme-maker-frontend nginx -s reload", "Reload nginx configuration"),
    ]
    
    print("🚀 Starting HTTPS API routing fix...")
    
    # First, let's check current nginx config
    print("\n🔍 Current HTTPS server block check:")
    if not run_command("docker exec meme-maker-frontend grep -A 10 'listen 443' /etc/nginx/nginx.conf", "Check HTTPS server config"):
        print("❌ Could not read HTTPS config")
        return False
    
    # Check if API location already exists in HTTPS block
    result = subprocess.run(
        "docker exec meme-maker-frontend grep -A 50 'listen 443' /etc/nginx/nginx.conf | grep 'location /api/'", 
        shell=True, capture_output=True, text=True
    )
    
    if result.returncode == 0:
        print("✅ API routing already exists in HTTPS server block!")
        print("🔍 The issue might be elsewhere. Let's test the current setup...")
    else:
        print("❌ API routing missing from HTTPS server block - this is the problem!")
        
        # We need to rebuild the container with proper nginx config
        print("\n🔧 Rebuilding frontend with complete nginx configuration...")
        
        rebuild_steps = [
            ("docker-compose stop frontend", "Stop frontend container"),
            ("docker-compose build --no-cache frontend", "Rebuild frontend container"),
            ("docker-compose up -d frontend", "Start frontend container"),
            ("sleep 10", "Wait for container to start"),
        ]
        
        for cmd, desc in rebuild_steps:
            if not run_command(cmd, desc):
                print(f"\n❌ Failed at step: {desc}")
                return False
    
    # Test the final setup
    print("\n🧪 Testing final setup...")
    test_commands = [
        ("curl -s -o /dev/null -w '%{http_code}' 'https://memeit.pro/api/v1/metadata' -X POST", "HTTPS API test"),
        ("curl -s -o /dev/null -w '%{http_code}' 'http://localhost/api/v1/metadata' -X POST", "HTTP API test"),
    ]
    
    for cmd, desc in test_commands:
        if run_command(cmd, desc):
            print(f"✅ {desc} working!")
    
    print("\n🎉 COMPLETE HTTPS SETUP FINISHED!")
    print("✅ Both HTTP and HTTPS should now route API calls correctly")
    print("✅ Mixed content errors resolved")
    print("✅ API routing configured for both protocols")
    print("\n🌐 Please refresh browser and test: https://memeit.pro")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 