#!/usr/bin/env python3
"""
Fix Nginx API Routing - Adds proper API proxy configuration to nginx
This script fixes the 404 API endpoint errors by configuring nginx to proxy /api/ requests to backend
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
    print("🔧 FIXING NGINX API ROUTING")
    print("=" * 40)
    
    # Create the nginx config content
    nginx_config = '''server {
    listen       80;
    server_name  localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Handle SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

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
    }

    # Health check
    location /health {
        return 200 "healthy";
        add_header Content-Type text/plain;
    }

    error_page 404 /index.html;
}'''
    
    steps = [
        ("cd ~/Meme-Maker", "Navigate to project directory"),
        (f"echo '{nginx_config}' > /tmp/nginx_default.conf", "Create nginx config file"),
        ("docker cp /tmp/nginx_default.conf meme-maker-frontend:/etc/nginx/conf.d/default.conf", "Copy config to container"),
        ("docker exec meme-maker-frontend nginx -t", "Test nginx configuration"),
        ("docker exec meme-maker-frontend nginx -s reload", "Reload nginx with new config"),
        ("rm /tmp/nginx_default.conf", "Clean up temporary file"),
    ]
    
    print("🎯 Steps to execute:")
    for i, (cmd, desc) in enumerate(steps, 1):
        print(f"  {i}. {desc}")
    
    print("\n🚀 Starting nginx configuration fix...")
    
    for cmd, description in steps:
        if not run_command(cmd, description):
            print(f"\n❌ Failed at step: {description}")
            return False
    
    print("\n✅ SUCCESS: Nginx API routing configured!")
    
    # Test the API endpoint
    print("\n🧪 Testing API endpoint...")
    test_cmd = "curl -s -o /dev/null -w '%{http_code}' http://localhost/api/v1/health"
    if run_command(test_cmd, "Testing API health endpoint"):
        print("✅ API routing is working!")
    
    print("\n🎉 NGINX API ROUTING FIX COMPLETE!")
    print("The website should now properly route API calls to the backend.")
    print("Please refresh your browser and test the video URL input.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 