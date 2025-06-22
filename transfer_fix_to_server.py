#!/usr/bin/env python3
"""
Transfer Fix Script to Production Server
Helps you get the fix script onto your AWS Lightsail server
"""

import os
import subprocess

def main():
    print("🚀 TRANSFER FIX SCRIPT TO PRODUCTION SERVER")
    print("=" * 50)
    print()
    
    # Check if fix script exists locally
    if not os.path.exists('fix_production_config.py'):
        print("❌ fix_production_config.py not found in current directory")
        print("   Make sure you're in the Meme-Maker directory")
        return
    
    print("✅ Found fix_production_config.py locally")
    print()
    
    print("📋 TRANSFER OPTIONS:")
    print("1. SCP transfer (if you have SSH key)")
    print("2. Copy-paste method (manual)")
    print()
    
    choice = input("Choose option (1 or 2): ").strip()
    
    if choice == "1":
        print("\n🔧 SCP TRANSFER METHOD")
        print("You'll need your SSH key file path")
        print()
        
        key_path = input("Enter path to your SSH key file (e.g., ~/.ssh/lightsail-key.pem): ").strip()
        
        if not key_path:
            print("❌ No key path provided")
            return
        
        # Expand user path
        key_path = os.path.expanduser(key_path)
        
        if not os.path.exists(key_path):
            print(f"❌ SSH key not found at: {key_path}")
            return
        
        print(f"✅ Found SSH key at: {key_path}")
        print()
        
        # SCP command
        scp_cmd = f'scp -i "{key_path}" fix_production_config.py ubuntu@13.126.173.223:~/Meme-Maker/'
        
        print("🚀 Running SCP transfer...")
        print(f"Command: {scp_cmd}")
        print()
        
        try:
            result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ File transferred successfully!")
                print()
                print("🎯 NEXT STEPS:")
                print("1. SSH into your server:")
                print(f'   ssh -i "{key_path}" ubuntu@13.126.173.223')
                print("2. Navigate to project directory:")
                print("   cd ~/Meme-Maker")
                print("3. Run the fix:")
                print("   python3 fix_production_config.py")
            else:
                print("❌ SCP transfer failed:")
                print(result.stderr)
                print("\n💡 Try the copy-paste method instead (option 2)")
        except Exception as e:
            print(f"❌ Error during transfer: {e}")
            print("\n💡 Try the copy-paste method instead (option 2)")
    
    elif choice == "2":
        print("\n📋 COPY-PASTE METHOD")
        print("Follow these steps:")
        print()
        print("1. SSH into your server:")
        print("   ssh -i /path/to/your/key.pem ubuntu@13.126.173.223")
        print("   (or use Lightsail browser SSH)")
        print()
        print("2. Navigate to project directory:")
        print("   cd ~/Meme-Maker")
        print()
        print("3. Create the fix script:")
        print("   nano fix_production_config.py")
        print()
        print("4. Copy the content from fix_production_config.py and paste it")
        print("   (Select all content in the file, Ctrl+C, then paste in nano)")
        print()
        print("5. Save and exit nano:")
        print("   Ctrl+X, then Y, then Enter")
        print()
        print("6. Make it executable:")
        print("   chmod +x fix_production_config.py")
        print()
        print("7. Run the fix:")
        print("   python3 fix_production_config.py")
        print()
        
        input("Press Enter when you've completed these steps...")
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main() 