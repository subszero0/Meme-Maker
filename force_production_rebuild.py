#!/usr/bin/env python3
"""
Force Production Rebuild - Ensures frontend is built correctly for production
This script fixes the localhost API calls by ensuring proper build environment
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
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)
        if result.stdout:
            print(f"✅ Output: {result.stdout}")
        if result.stderr and result.returncode != 0:
            print(f"❌ Error: {result.stderr}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"⏰ Command timed out after 10 minutes")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("🚀 FORCE PRODUCTION REBUILD")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("docker-compose.yaml"):
        print("❌ Error: docker-compose.yaml not found")
        print("   Please run this from the Meme-Maker directory")
        sys.exit(1)
    
    print("✅ Found docker-compose.yaml - we're in the right place")
    
    # Step 1: Stop only frontend
    print("\n🛑 STEP 1: Stopping frontend container")
    if not run_command("docker-compose stop frontend", "Stopping frontend"):
        print("❌ Failed to stop frontend")
        sys.exit(1)
    
    # Step 2: Remove frontend container and image
    print("\n🗑️ STEP 2: Removing frontend container and image")
    run_command("docker-compose rm -f frontend", "Removing frontend container")
    run_command("docker rmi meme-maker_frontend 2>/dev/null || true", "Removing frontend image")
    
    # Step 3: Clear all Docker caches
    print("\n🧹 STEP 3: Clearing Docker cache")
    run_command("docker builder prune -f", "Clearing builder cache")
    run_command("docker system prune -f", "Clearing system cache")
    
    # Step 4: Build frontend with explicit production environment
    print("\n🔨 STEP 4: Building frontend with explicit production config")
    build_cmd = """
docker build --no-cache \
  --build-arg NODE_ENV=production \
  --build-arg MODE=production \
  --build-arg VITE_MODE=production \
  -t meme-maker_frontend \
  ./frontend-new
"""
    if not run_command(build_cmd, "Building frontend with production environment"):
        print("❌ Failed to build frontend")
        sys.exit(1)
    
    # Step 5: Start frontend
    print("\n🚀 STEP 5: Starting frontend container")
    if not run_command("docker-compose up -d frontend", "Starting frontend"):
        print("❌ Failed to start frontend")
        sys.exit(1)
    
    # Step 6: Wait for frontend to be ready
    print("\n⏳ STEP 6: Waiting for frontend to start (30 seconds)")
    time.sleep(30)
    
    # Step 7: Test the build
    print("\n🧪 STEP 7: Testing the frontend build")
    test_cmd = "docker exec meme-maker-frontend find /usr/share/nginx/html -name '*.js' -exec grep -l 'localhost:8000' {} \\;"
    result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout.strip():
        print("❌ Frontend still contains localhost:8000 references!")
        print("   Files with localhost references:")
        print(result.stdout)
        print("\n🔧 Let's try a different approach...")
        
        # Alternative approach: Modify the environment config directly
        print("\n🛠️ STEP 8: Modifying environment config directly")
        
        # Create a patched environment file
        patch_cmd = """
docker exec meme-maker-frontend sh -c '
find /usr/share/nginx/html -name "*.js" -exec sed -i "s|localhost:8000|/api|g" {} \\;
find /usr/share/nginx/html -name "*.js" -exec sed -i "s|http://localhost:8000|/api|g" {} \\;
find /usr/share/nginx/html -name "*.js" -exec sed -i "s|https://localhost:8000|/api|g" {} \\;
'
"""
        if run_command(patch_cmd, "Patching localhost references in built files"):
            print("✅ Patched localhost references!")
        else:
            print("⚠️ Patch failed, but container is running")
            
    else:
        print("✅ No localhost:8000 references found in build!")
    
    # Step 8: Final test
    print("\n🔍 STEP 9: Final status check")
    run_command("docker ps | grep frontend", "Checking frontend status")
    
    print("\n" + "=" * 50)
    print("🏁 FORCE REBUILD COMPLETE")
    print("🌐 Test your site: https://memeit.pro")
    print("🔄 If still seeing localhost errors, try a hard refresh (Ctrl+F5)")

if __name__ == "__main__":
    main() 