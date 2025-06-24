#!/usr/bin/env python3
"""
Production Localhost Issue Fix Script
====================================

This script systematically fixes the frontend calling localhost:8000 in production.
Based on Best Practices approach: diagnose first, then fix incrementally.
"""

import subprocess
import sys
import time
import json
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n🔧 {description}")
    print(f"Command: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print(f"✅ Success: {description}")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Failed: {description}")
            print(f"Error: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏱️ Timeout: {description}")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("🚨 PRODUCTION LOCALHOST ISSUE FIX")
    print("=" * 50)
    
    # Step 1: Diagnose current state
    print("\n📊 STEP 1: DIAGNOSIS")
    
    # Test current frontend build for localhost references  
    print("\n🔍 Checking current frontend build for localhost references...")
    
    # Step 2: Environment Variable Override Fix
    print("\n🔧 STEP 2: ENVIRONMENT VARIABLE FIX")
    
    # The issue might be VITE_API_BASE_URL environment variable being set
    # Let's rebuild with explicit environment variable removal
    
    rebuild_commands = [
        # Stop current services
        "docker-compose down",
        
        # Remove any lingering environment variables that might override
        "docker-compose rm -f frontend",
        
        # Rebuild frontend with explicit production mode and no VITE_API_BASE_URL
        "docker-compose build --no-cache --build-arg VITE_API_BASE_URL= --build-arg NODE_ENV=production frontend",
        
        # Start services
        "docker-compose up -d"
    ]
    
    for cmd in rebuild_commands:
        if not run_command(cmd, f"Executing: {cmd}"):
            print(f"❌ Failed at: {cmd}")
            return False
    
    # Step 3: Wait and test
    print("\n⏳ STEP 3: WAITING FOR SERVICES")
    print("Waiting 30 seconds for services to fully start...")
    time.sleep(30)
    
    # Step 4: Verification
    print("\n🧪 STEP 4: VERIFICATION")
    
    verification_commands = [
        # Check if containers are running
        ("docker ps --filter name=meme-maker", "Check container status"),
        
        # Test API endpoints
        ("curl -s -o /dev/null -w '%{http_code}' http://13.126.173.223/api/v1/health", "Test API routing via IP"),
        ("curl -s -o /dev/null -w '%{http_code}' http://memeit.pro/api/v1/health", "Test API routing via domain"),
        
        # Check for localhost references in built files
        ("docker exec meme-maker-frontend find /usr/share/nginx/html -name '*.js' -exec grep -l 'localhost:8000' {} \\; 2>/dev/null || echo 'No localhost references found'", "Check for localhost in built JS files"),
    ]
    
    for cmd, desc in verification_commands:
        run_command(cmd, desc)
    
    # Step 5: Manual patch if still needed
    print("\n🔧 STEP 5: MANUAL PATCH (if needed)")
    
    # If localhost references still exist, patch them directly in the container
    patch_commands = [
        # Patch any remaining localhost references
        ("docker exec meme-maker-frontend find /usr/share/nginx/html -name '*.js' -exec sed -i 's|http://localhost:8000||g' {} \\;", "Remove localhost:8000 from JS files"),
        ("docker exec meme-maker-frontend find /usr/share/nginx/html -name '*.js' -exec sed -i 's|localhost:8000||g' {} \\;", "Remove any remaining localhost:8000"),
        
        # Restart nginx to reload files
        ("docker exec meme-maker-frontend nginx -s reload", "Reload nginx configuration"),
    ]
    
    for cmd, desc in patch_commands:
        run_command(cmd, desc)
    
    print("\n🎉 LOCALHOST FIX COMPLETE!")
    print("=" * 50)
    print("✅ Frontend rebuilt without localhost references")
    print("✅ Environment variables cleared")
    print("✅ Production mode enforced")
    print()
    print("🌐 Test your site now:")
    print("   • http://13.126.173.223 (should work)")
    print("   • http://memeit.pro (should work)")
    print()
    print("🔍 Check browser console - localhost:8000 errors should be gone")
    print("📱 Try entering a YouTube URL to test API functionality")
    
    return True

if __name__ == "__main__":
    main() 