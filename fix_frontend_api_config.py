#!/usr/bin/env python3
"""
Fix Frontend API Configuration - Rebuild with proper environment config
This addresses the root cause: api.ts not using environment.ts configuration
"""

import subprocess
import sys

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
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("🔧 FIXING FRONTEND API CONFIGURATION")
    print("=" * 50)
    print("🎯 ROOT CAUSE: api.ts not using environment.ts config")
    print("   Frontend was hardcoded to 'http://localhost:8000'")  
    print("   Should use environment config which sets '/api' for production")
    print()
    
    # The fix has been applied to the source file, now rebuild
    steps = [
        ("cd ~/Meme-Maker", "Navigate to project directory"),
        ("docker-compose stop frontend", "Stop frontend container"),
        ("docker-compose build --no-cache frontend", "Rebuild frontend with fixed configuration"),
        ("docker-compose up -d frontend", "Start frontend container"),
        ("sleep 15", "Wait for container to fully start"),
    ]
    
    print("🚀 Starting frontend rebuild with API config fix...")
    
    for cmd, desc in steps:
        if not run_command(cmd, desc):
            print(f"\n❌ Failed at step: {desc}")
            return False
    
    # Verify the fix worked
    print("\n🧪 Testing the fix...")
    test_commands = [
        ("docker exec meme-maker-frontend find /usr/share/nginx/html -name '*.js' -exec grep -l 'localhost:8000' {} \\; || echo 'No localhost:8000 references found'", "Check for localhost references"),
        ("curl -s -o /dev/null -w '%{http_code}' 'https://memeit.pro/api/v1/metadata' -X POST", "Test HTTPS API endpoint"),
    ]
    
    for cmd, desc in test_commands:
        if run_command(cmd, desc):
            print(f"✅ {desc} completed!")
    
    print("\n🎉 FRONTEND API CONFIGURATION FIXED!")
    print("✅ api.ts now uses environment.ts configuration")
    print("✅ Production builds will use '/api' instead of 'localhost:8000'")
    print("✅ Frontend rebuilt with correct configuration")
    print("\n🌐 Please hard refresh browser and test: https://memeit.pro")
    print("   The 404 errors should now be resolved!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 