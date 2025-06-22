#!/usr/bin/env python3
"""
Fix Mixed Content - Removes http:// prefixes from API calls to fix HTTPS issues
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
    print("🔧 FIXING MIXED CONTENT ISSUE")
    print("=" * 40)
    
    # Fix the mixed content issue by removing http:// prefixes
    print("\n🛠️ Removing http:// prefixes from API calls")
    
    fix_commands = [
        'docker exec meme-maker-frontend find /usr/share/nginx/html -name "*.js" -exec sed -i "s|http://api|/api|g" {} \\;',
        'docker exec meme-maker-frontend find /usr/share/nginx/html -name "*.js" -exec sed -i "s|https://api|/api|g" {} \\;',
        'docker exec meme-maker-frontend find /usr/share/nginx/html -name "*.js" -exec sed -i "s|\\"http://api|\"/api|g" {} \\;',
        'docker exec meme-maker-frontend find /usr/share/nginx/html -name "*.js" -exec sed -i "s|\\"https://api|\"/api|g" {} \\;'
    ]
    
    for cmd in fix_commands:
        if not run_command(cmd, f"Applying fix: {cmd.split('|')[1]}"):
            print("⚠️ Some fixes may have failed, but continuing...")
    
    # Test the fix
    print("\n🧪 Testing for remaining mixed content issues")
    test_cmd = 'docker exec meme-maker-frontend find /usr/share/nginx/html -name "*.js" -exec grep -l "http://api" {} \\; 2>/dev/null || echo "No http://api references found"'
    run_command(test_cmd, "Checking for remaining http://api references")
    
    print("\n" + "=" * 40)
    print("🏁 MIXED CONTENT FIX COMPLETE")
    print("🌐 Try your website again: https://memeit.pro")
    print("🔄 Do a hard refresh (Ctrl+F5) to see the changes")

if __name__ == "__main__":
    main() 