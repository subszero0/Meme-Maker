#!/usr/bin/env python3
"""
Instagram URL Extraction Test and Fix
Tests the failing Instagram URLs and implements solutions
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'worker'))

from utils.ytdlp_options import build_instagram_ydl_configs, is_instagram_url
import yt_dlp
import json

# The three failing URLs from the user
FAILING_URLS = [
    "https://www.instagram.com/reel/DLfPgczIp-x/?igsh=NWExNzlwb3h5YnJn",
    "https://www.instagram.com/reel/DLjuZlDTrq3/?igsh=MXIxNGNrenp4bGF5aw==", 
    "https://www.instagram.com/reel/DLiGaJABO_a/?igsh=MWQwc3BqcHA2M2k3Mw=="
]

def test_direct_ytdlp(url):
    """Test with basic yt-dlp to see raw Instagram behavior"""
    print(f"\n🔍 Testing direct yt-dlp for: {url}")
    
    basic_config = {
        "quiet": False,
        "extract_flat": False,
    }
    
    try:
        with yt_dlp.YoutubeDL(basic_config) as ydl:
            info = ydl.extract_info(url, download=False)
            print(f"✅ DIRECT SUCCESS: {info.get('title', 'Unknown')}")
            return True
    except Exception as e:
        print(f"❌ DIRECT FAILED: {str(e)}")
        return False

def test_current_configs(url):
    """Test with current Instagram configurations"""
    print(f"\n🔧 Testing current Instagram configs for: {url}")
    
    if not is_instagram_url(url):
        print("❌ URL not recognized as Instagram URL")
        return False
    
    configs = build_instagram_ydl_configs()
    print(f"📋 Built {len(configs)} configurations")
    
    for i, config in enumerate(configs, 1):
        print(f"\n🧪 Trying config {i}/{len(configs)}...")
        try:
            with yt_dlp.YoutubeDL(config) as ydl:
                info = ydl.extract_info(url, download=False)
                print(f"✅ SUCCESS with config {i}!")
                print(f"📝 Title: {info.get('title', 'Unknown')}")
                print(f"⏱️ Duration: {info.get('duration', 'Unknown')}")
                return True
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Config {i} failed: {error_msg[:150]}...")
            
            # Check specific error types
            if "login required" in error_msg.lower():
                print("   🔐 Login/Authentication required")
            elif "rate" in error_msg.lower():
                print("   ⏳ Rate limiting detected") 
            elif "unavailable" in error_msg.lower():
                print("   🚫 Content unavailable")
            elif "private" in error_msg.lower():
                print("   🔒 Private content")
    
    print("❌ All configurations failed")
    return False

def main():
    print("🧪 Instagram URL Extraction Diagnostic")
    print("=" * 50)
    
    results = {}
    
    for url in FAILING_URLS:
        print(f"\n{'='*60}")
        print(f"Testing URL: {url}")
        print(f"{'='*60}")
        
        url_results = {
            "direct": test_direct_ytdlp(url),
            "current": test_current_configs(url), 
        }
        
        results[url] = url_results
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}")
    
    for url, url_results in results.items():
        print(f"\n📋 {url}:")
        for method, success in url_results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {method}: {status}")
        
if __name__ == "__main__":
    main() 