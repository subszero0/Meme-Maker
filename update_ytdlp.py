#!/usr/bin/env python3
"""
Update yt-dlp in Docker containers to fix YouTube blocking issues.
"""

import subprocess
import sys

def run_command(cmd, description):
    """Run a command and show the result"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed:")
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} timed out")
        return False
    except Exception as e:
        print(f"❌ {description} error: {e}")
        return False

def main():
    print("🔄 yt-dlp Update Script")
    print("=" * 40)
    print("This will update yt-dlp in Docker containers to fix YouTube blocking.")
    print()
    
    # Update worker container
    commands = [
        ("docker-compose exec worker pip install --upgrade yt-dlp", "Updating yt-dlp in worker container"),
        ("docker-compose exec backend pip install --upgrade yt-dlp", "Updating yt-dlp in backend container (if needed)"),
    ]
    
    success_count = 0
    for cmd, desc in commands:
        if run_command(cmd, desc):
            success_count += 1
    
    print("\n" + "=" * 40)
    if success_count == len(commands):
        print("✅ yt-dlp update completed successfully!")
        print("🔄 Restart containers to apply changes:")
        print("   docker-compose restart worker backend")
    else:
        print("⚠️  Some updates failed. You can also rebuild containers:")
        print("   docker-compose down")
        print("   docker-compose up --build")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 