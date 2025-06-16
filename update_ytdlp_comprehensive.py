#!/usr/bin/env python3
"""
Comprehensive yt-dlp update script to fix YouTube blocking issues.
"""

import subprocess
import sys
import time
import requests

def run_command(cmd, description, timeout=120):
    """Run a command and show the result"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout.strip():
                # Show relevant output (last few lines)
                output_lines = result.stdout.strip().split('\n')
                for line in output_lines[-3:]:  # Show last 3 lines
                    if line.strip():
                        print(f"   📋 {line.strip()}")
            return True
        else:
            print(f"❌ {description} failed:")
            if result.stderr:
                print(f"   📋 Error: {result.stderr.strip()}")
            if result.stdout:
                print(f"   📋 Output: {result.stdout.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} timed out after {timeout} seconds")
        return False
    except Exception as e:
        print(f"❌ {description} error: {e}")
        return False

def check_containers_running():
    """Check if Docker containers are running"""
    print("🔍 Checking Docker container status...")
    
    result = subprocess.run("docker-compose ps", shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Docker Compose not running or failed")
        return False
    
    # Check if worker and backend are running
    if "worker" in result.stdout and "backend" in result.stdout:
        print("✅ Docker containers are running")
        return True
    else:
        print("❌ Required containers (worker, backend) not running")
        print("💡 Run: docker-compose up -d")
        return False

def update_ytdlp_in_containers():
    """Update yt-dlp in all relevant containers"""
    commands = [
        # Update in worker container (most important)
        ("docker-compose exec -T worker pip install --upgrade --force-reinstall yt-dlp", 
         "Updating yt-dlp in worker container"),
        
        # Update in backend container (for metadata extraction)
        ("docker-compose exec -T backend pip install --upgrade --force-reinstall yt-dlp", 
         "Updating yt-dlp in backend container"),
    ]
    
    success_count = 0
    for cmd, desc in commands:
        if run_command(cmd, desc):
            success_count += 1
    
    return success_count == len(commands)

def get_ytdlp_version_in_container(container):
    """Get yt-dlp version in a specific container"""
    try:
        result = subprocess.run(
            f"docker-compose exec -T {container} python -c \"import yt_dlp; print(yt_dlp.version.__version__)\"",
            shell=True, capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return "Unknown"
    except:
        return "Error"

def test_ytdlp_update():
    """Test if yt-dlp update was successful"""
    print("\n🧪 Testing yt-dlp update...")
    
    # Check versions
    worker_version = get_ytdlp_version_in_container("worker")
    backend_version = get_ytdlp_version_in_container("backend")
    
    print(f"📋 Worker yt-dlp version: {worker_version}")
    print(f"📋 Backend yt-dlp version: {backend_version}")
    
    # Test basic functionality with a simple URL
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # Me at the zoo
    print(f"\n🔍 Testing yt-dlp functionality with: {test_url}")
    
    # Test in worker container
    test_cmd = f"""docker-compose exec -T worker python -c "
import yt_dlp
import json

ydl_opts = {{
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
}}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info('{test_url}', download=False)
        print(f'SUCCESS: Title={{info.get(\\"title\\", \\"Unknown\\")}}')
        print(f'SUCCESS: Formats={{len(info.get(\\"formats\\", []))}}')
except Exception as e:
    print(f'ERROR: {{str(e)}}')
"""
    
    result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True, timeout=60)
    
    if result.returncode == 0 and "SUCCESS:" in result.stdout:
        print("✅ yt-dlp update test successful!")
        return True
    else:
        print("❌ yt-dlp update test failed:")
        if result.stdout:
            print(f"   📋 Output: {result.stdout.strip()}")
        if result.stderr:
            print(f"   📋 Error: {result.stderr.strip()}")
        return False

def restart_containers():
    """Restart containers to apply changes"""
    print("\n🔄 Restarting containers to apply yt-dlp updates...")
    
    commands = [
        ("docker-compose restart worker", "Restarting worker container"),
        ("docker-compose restart backend", "Restarting backend container"),
    ]
    
    success_count = 0
    for cmd, desc in commands:
        if run_command(cmd, desc, timeout=60):
            success_count += 1
    
    if success_count == len(commands):
        print("✅ Containers restarted successfully")
        # Wait for services to be ready
        print("⏳ Waiting for services to be ready...")
        time.sleep(10)
        return True
    else:
        print("⚠️  Some containers failed to restart")
        return False

def main():
    print("🔄 YouTube Blocking Fix - yt-dlp Update")
    print("=" * 50)
    print("This script will update yt-dlp to fix YouTube blocking issues.")
    print()
    
    # Step 1: Check if containers are running
    if not check_containers_running():
        print("\n💡 Please start Docker containers first:")
        print("   docker-compose up -d")
        return 1
    
    # Step 2: Update yt-dlp in containers
    print("\n📦 Updating yt-dlp...")
    if not update_ytdlp_in_containers():
        print("\n⚠️  yt-dlp update had issues, but continuing...")
    
    # Step 3: Restart containers
    if not restart_containers():
        print("\n⚠️  Container restart had issues")
        return 1
    
    # Step 4: Test the update
    if test_ytdlp_update():
        print("\n🎉 SUCCESS: yt-dlp update completed successfully!")
        print("✅ YouTube blocking should be resolved")
        print("\n🎯 Next steps:")
        print("1. Run: python test_youtube_blocking.py")
        print("2. Test different resolutions with real YouTube videos")
    else:
        print("\n⚠️  yt-dlp update completed but test failed")
        print("💡 YouTube blocking may still be an issue")
        print("💡 Consider checking Docker logs: docker-compose logs worker")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 