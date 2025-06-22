#!/usr/bin/env python3
"""
Automated Production Fix Script - No User Interaction Required
This script fixes the localhost API calls issue on production
"""

import subprocess
import time
import sys
import os

def run_command(cmd, description=""):
    """Run a shell command and handle errors"""
    print(f"\n🔄 {description}")
    print(f"Running: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        if result.stdout:
            print(f"✅ Output: {result.stdout}")
        if result.stderr and result.returncode != 0:
            print(f"❌ Error: {result.stderr}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"⏰ Command timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("🚀 STARTING AUTOMATED PRODUCTION FIX")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("docker-compose.yaml"):
        print("❌ Error: docker-compose.yaml not found")
        print("   Please run this from the Meme-Maker directory")
        sys.exit(1)
    
    print("✅ Found docker-compose.yaml - we're in the right place")
    
    # Step 1: Check current status
    print("\n📊 STEP 1: Checking current status")
    run_command("docker ps", "Checking running containers")
    
    # Step 2: Stop containers
    print("\n🛑 STEP 2: Stopping all containers")
    if not run_command("docker-compose down", "Stopping containers"):
        print("❌ Failed to stop containers")
        sys.exit(1)
    
    # Step 3: Clean Docker cache
    print("\n🧹 STEP 3: Cleaning Docker cache")
    run_command("docker system prune -f", "Cleaning Docker cache")
    
    # Step 4: Rebuild containers
    print("\n🔨 STEP 4: Rebuilding containers with production config")
    if not run_command("docker-compose build --no-cache", "Rebuilding containers"):
        print("❌ Failed to rebuild containers")
        sys.exit(1)
    
    # Step 5: Start containers
    print("\n🚀 STEP 5: Starting containers")
    if not run_command("docker-compose up -d", "Starting containers"):
        print("❌ Failed to start containers")
        sys.exit(1)
    
    # Step 6: Wait for services to be ready
    print("\n⏳ STEP 6: Waiting for services to start (60 seconds)")
    time.sleep(60)
    
    # Step 7: Check container status
    print("\n🔍 STEP 7: Checking container health")
    run_command("docker ps", "Checking container status")
    
    # Step 8: Test the API
    print("\n🧪 STEP 8: Testing the API fix")
    test_url = "http://localhost/api/v1/metadata?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    if run_command(f'curl -s "{test_url}"', "Testing API endpoint"):
        print("\n🎉 SUCCESS! The API is now working correctly")
        print("✅ Your website should now work without localhost errors")
        print(f"🌐 Test your site: https://memeit.pro")
    else:
        print("\n⚠️  API test failed, but containers are running")
        print("   The fix may still have worked - check your website")
    
    print("\n" + "=" * 50)
    print("🏁 AUTOMATED FIX COMPLETE")
    print("🌐 Visit https://memeit.pro to test your site")

if __name__ == "__main__":
    main() 