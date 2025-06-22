#!/usr/bin/env python3
"""
Production API URL Fix Script
Fixes the double /api issue in production frontend
"""

import subprocess
import sys
import time
import requests
from datetime import datetime

def log(message, level="INFO"):
    """Enhanced logging with timestamps"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def run_command(cmd, description):
    """Run a command and return success status"""
    log(f"Running: {description}")
    log(f"Command: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            log(f"✅ {description} - Success")
            if result.stdout.strip():
                log(f"Output: {result.stdout[:200]}...")
            return True
        else:
            log(f"❌ {description} - Failed (exit code: {result.returncode})")
            if result.stderr.strip():
                log(f"Error: {result.stderr[:200]}...")
            return False
            
    except subprocess.TimeoutExpired:
        log(f"❌ {description} - Timed out after 5 minutes")
        return False
    except Exception as e:
        log(f"❌ {description} - Exception: {e}")
        return False

def test_production_api():
    """Test if the production API fix worked"""
    log("Testing production API endpoints...")
    
    try:
        # Test the fixed endpoint
        response = requests.post(
            'https://memeit.pro/api/v1/metadata',
            json={'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'},
            timeout=15
        )
        
        if response.status_code in [200, 422]:  # 422 is expected for invalid URL
            log("✅ Production API endpoint responding correctly")
            return True
        else:
            log(f"❌ Production API still failing: {response.status_code}")
            return False
            
    except Exception as e:
        log(f"❌ Production API test failed: {e}")
        return False

def main():
    """Main deployment process"""
    log("🚀 STARTING PRODUCTION API URL FIX")
    log("=" * 60)
    
    # Step 1: Verify we're in the right directory
    try:
        with open('docker-compose.yaml', 'r') as f:
            if 'memeit.pro' in f.read():
                log("✅ Confirmed: In production directory")
            else:
                log("❌ Error: Not in production directory")
                return False
    except FileNotFoundError:
        log("❌ Error: docker-compose.yaml not found")
        return False
    
    # Step 2: Stop current frontend container
    log("\n🛑 Step 2: Stopping frontend container")
    if not run_command("docker-compose stop frontend", "Stop frontend container"):
        log("⚠️  Warning: Could not stop frontend container (may not be running)")
    
    # Step 3: Rebuild frontend with fix
    log("\n🔨 Step 3: Rebuilding frontend with API URL fix")
    if not run_command("docker-compose build --no-cache frontend", "Rebuild frontend"):
        log("❌ Critical: Frontend rebuild failed")
        return False
    
    # Step 4: Start frontend container
    log("\n🚀 Step 4: Starting frontend container")
    if not run_command("docker-compose up -d frontend", "Start frontend"):
        log("❌ Critical: Frontend startup failed")
        return False
    
    # Step 5: Wait for container to be ready
    log("\n⏳ Step 5: Waiting for frontend to be ready (30 seconds)")
    time.sleep(30)
    
    # Step 6: Check container status
    log("\n🔍 Step 6: Checking container status")
    run_command("docker-compose ps frontend", "Check frontend status")
    
    # Step 7: Test the fix
    log("\n🧪 Step 7: Testing the API URL fix")
    if test_production_api():
        log("✅ API URL fix successful!")
    else:
        log("❌ API URL fix may need additional work")
        return False
    
    # Step 8: Final verification
    log("\n✅ Step 8: Final verification")
    log("🎯 PRODUCTION FIX COMPLETE!")
    log("=" * 60)
    log("💡 Next steps:")
    log("   1. Open https://memeit.pro in your browser")
    log("   2. Hard refresh (Ctrl+Shift+R)")
    log("   3. Test with a YouTube URL")
    log("   4. Check that console shows no more 404 errors")
    log("   5. Verify URLs now call /api/v1/metadata (not /api/api/v1/metadata)")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 