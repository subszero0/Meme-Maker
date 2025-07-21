#!/usr/bin/env python3

import yt_dlp
import sys

def test_instagram_url(url, label):
    """Test Instagram URL extraction with detailed error reporting"""
    print(f"\n{'='*60}")
    print(f"🔍 Testing {label}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    # Configure yt-dlp similar to backend
    ydl_opts = {
        'quiet': False,  # Enable verbose output for debugging
        'no_warnings': False,
        'extract_flat': False,
        'socket_timeout': 120,
        'retries': 3,
    }
    
    ydl = yt_dlp.YoutubeDL(ydl_opts)
    
    try:
        print(f"⏳ Extracting metadata...")
        info = ydl.extract_info(url, download=False)
        
        print(f"✅ SUCCESS for {label}!")
        print(f"   Title: {info.get('title', 'No title')}")
        print(f"   Duration: {info.get('duration', 'No duration')} seconds")
        print(f"   Uploader: {info.get('uploader', 'No uploader')}")
        print(f"   View count: {info.get('view_count', 'No view count')}")
        print(f"   Formats available: {len(info.get('formats', []))}")
        
        # Check for any unusual properties
        if 'availability' in info:
            print(f"   Availability: {info['availability']}")
        if 'live_status' in info:
            print(f"   Live status: {info['live_status']}")
        if 'is_live' in info:
            print(f"   Is live: {info['is_live']}")
            
        return True
        
    except Exception as e:
        print(f"❌ FAILURE for {label}!")
        print(f"   Error: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        
        # Analyze error patterns
        error_str = str(e).lower()
        if 'unavailable' in error_str:
            print(f"   🔍 ANALYSIS: Content appears to be unavailable")
        elif 'private' in error_str:
            print(f"   🔍 ANALYSIS: Content appears to be private")
        elif 'deleted' in error_str:
            print(f"   🔍 ANALYSIS: Content appears to be deleted")
        elif 'login' in error_str or 'authentication' in error_str:
            print(f"   🔍 ANALYSIS: Authentication required")
        else:
            print(f"   🔍 ANALYSIS: Unknown error pattern")
            
        return False

def main():
    """Test both URLs and compare results"""
    
    # Test URLs
    working_url = "https://www.instagram.com/reel/DLjuZlDTrq3/?igsh=MXIxNGNrenp4bGF5aw=="
    failing_url = "https://www.instagram.com/reel/DLiGaJABO_a/?igsh=MWQwc3BqcHA2M2k3Mw=="
    
    print("🧪 Instagram URL Comparison Test")
    print("This will help identify why one URL works and another fails")
    
    # Test working URL
    working_result = test_instagram_url(working_url, "WORKING URL")
    
    # Test failing URL  
    failing_result = test_instagram_url(failing_url, "FAILING URL")
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 COMPARISON SUMMARY")
    print(f"{'='*60}")
    print(f"Working URL Result: {'✅ SUCCESS' if working_result else '❌ FAILED'}")
    print(f"Failing URL Result: {'✅ SUCCESS' if failing_result else '❌ FAILED'}")
    
    if working_result and not failing_result:
        print("\n🔍 ROOT CAUSE HYPOTHESIS:")
        print("   The failing URL likely points to:")
        print("   - Deleted/removed content")
        print("   - Private content")  
        print("   - Age-restricted content")
        print("   - Content with different availability settings")
        print("\n💡 SOLUTION:")
        print("   Backend should return appropriate HTTP status codes")
        print("   based on the specific yt-dlp error type")
    elif not working_result and not failing_result:
        print("\n🔍 ROOT CAUSE HYPOTHESIS:")
        print("   Both URLs fail - this suggests a broader issue")
    elif working_result and failing_result:
        print("\n🔍 ROOT CAUSE HYPOTHESIS:")
        print("   Both URLs work locally - production environment issue")

if __name__ == '__main__':
    main() 