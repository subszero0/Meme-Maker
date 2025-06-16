#!/usr/bin/env python3
"""
Test backend metadata endpoint to debug format mismatch
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"
TEST_URL = "https://www.youtube.com/watch?v=vEy6tcU6eLU"

def test_backend_metadata():
    """Test the backend metadata extraction endpoint"""
    print(f"🔍 Testing backend metadata extraction for: {TEST_URL}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/metadata/extract",
            json={"url": TEST_URL},
            timeout=60
        )
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Backend metadata extraction failed: {response.status_code}")
            print(f"📋 Response text: {response.text}")
            return False
        
        data = response.json()
        formats = data.get('formats', [])
        
        print(f"✅ Backend returned {len(formats)} formats")
        print(f"📋 Video title: {data.get('title', 'Unknown')}")
        print(f"📋 Duration: {data.get('duration', 'Unknown')} seconds")
        
        if formats:
            print(f"\n📋 Formats returned by backend:")
            for i, fmt in enumerate(formats):
                format_id = fmt.get('format_id', 'unknown')
                resolution = fmt.get('resolution', 'unknown')
                filesize = fmt.get('filesize')
                size_str = f"({filesize // 1024 // 1024:.1f}MB)" if filesize else "(unknown size)"
                vcodec = fmt.get('vcodec', 'unknown')
                acodec = fmt.get('acodec', 'unknown')
                
                print(f"  {i+1}. {format_id} - {resolution} {size_str} - {vcodec}/{acodec}")
                
                # Check if format 232 is in the list
                if format_id == '232':
                    print(f"  🎯 Found format 232 in backend response!")
        else:
            print("❌ No formats found in backend response")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing backend: {e}")
        return False

def test_local_ytdlp():
    """Test local yt-dlp to compare with backend"""
    print(f"\n🔍 Testing local yt-dlp for comparison...")
    
    try:
        import yt_dlp
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(TEST_URL, download=False)
            
            if 'entries' in info and info['entries']:
                info = info['entries'][0]
            
            formats = info.get('formats', [])
            
            print(f"✅ Local yt-dlp found {len(formats)} formats")
            
            # Filter to video formats only
            video_formats = []
            for fmt in formats:
                if (fmt.get('vcodec') != 'none' and 
                    fmt.get('height') and 
                    fmt.get('width')):
                    video_formats.append(fmt)
            
            print(f"📋 Video formats found locally:")
            for i, fmt in enumerate(video_formats[:10]):  # Show first 10
                format_id = fmt.get('format_id', 'unknown')
                width = fmt.get('width', 0)
                height = fmt.get('height', 0)
                resolution = f"{width}x{height}" if width and height else 'unknown'
                filesize = fmt.get('filesize')
                size_str = f"({filesize // 1024 // 1024:.1f}MB)" if filesize else "(unknown size)"
                vcodec = fmt.get('vcodec', 'unknown')
                acodec = fmt.get('acodec', 'unknown')
                
                print(f"  {i+1}. {format_id} - {resolution} {size_str} - {vcodec}/{acodec}")
                
                # Check if format 232 is available locally
                if format_id == '232':
                    print(f"  🎯 Found format 232 in local yt-dlp!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing local yt-dlp: {e}")
        return False

def main():
    """Run both tests and compare results"""
    print("🚀 Testing backend vs local yt-dlp format extraction")
    print("=" * 60)
    
    backend_success = test_backend_metadata()
    local_success = test_local_ytdlp()
    
    print("\n" + "=" * 60)
    if backend_success and local_success:
        print("✅ Both tests completed - compare the format lists above")
        print("🔍 Key question: Does backend show format 232 when local yt-dlp doesn't?")
    elif not backend_success:
        print("❌ Backend test failed - this explains the frontend issue")
    elif not local_success:
        print("❌ Local yt-dlp test failed - may be a yt-dlp issue")
    else:
        print("❌ Both tests failed")

if __name__ == "__main__":
    main() 