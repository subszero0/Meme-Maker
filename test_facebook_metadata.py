#!/usr/bin/env python3
"""
Test script to examine Facebook video metadata extraction and format data.
This will help diagnose why the video plays without audio.
"""
import json
import requests
import sys
from typing import Dict

def test_facebook_metadata_extraction():
    """Test metadata extraction for the problematic Facebook video."""
    
    # This is the video showing in the logs - getting parsing errors
    # We need to extract a Facebook URL from the logs first
    test_url = "https://www.facebook.com/reel/2797924943847507"  # Based on video ID in logs
    
    print("🔍 Testing Facebook video metadata extraction")
    print("=" * 60)
    print(f"📺 URL: {test_url}")
    print()
    
    # Test against local backend
    backend_url = "http://localhost:8000"
    
    try:
        print("🚀 Sending request to backend...")
        response = requests.post(
            f"{backend_url}/api/v1/metadata/extract",
            json={"url": test_url},
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ Backend returned {response.status_code}: {response.text}")
            return
            
        data = response.json()
        
        print("✅ Metadata extraction successful!")
        print(f"📽️ Title: {data.get('title', 'N/A')}")
        print(f"⏱️ Duration: {data.get('duration', 'N/A')} seconds")
        print(f"👤 Uploader: {data.get('uploader', 'N/A')}")
        print(f"🖼️ Thumbnail: {data.get('thumbnail', 'N/A')[:80]}...")
        print()
        
        formats = data.get('formats', [])
        print(f"🎯 Found {len(formats)} formats:")
        print("-" * 40)
        
        for i, fmt in enumerate(formats[:10]):  # Show first 10 formats
            format_id = fmt.get('format_id', 'unknown')
            ext = fmt.get('ext', 'unknown')
            resolution = fmt.get('resolution', 'unknown')
            vcodec = fmt.get('vcodec', 'none')
            acodec = fmt.get('acodec', 'none')
            filesize = fmt.get('filesize', 0)
            format_note = fmt.get('format_note', '')
            url = fmt.get('url', '')[:80] + '...' if fmt.get('url') else 'N/A'
            
            print(f"Format {i+1}:")
            print(f"  📋 ID: {format_id}")
            print(f"  📐 Resolution: {resolution}")
            print(f"  📄 Extension: {ext}")
            print(f"  🎬 Video Codec: {vcodec}")
            print(f"  🔊 Audio Codec: {acodec}")
            print(f"  📦 File Size: {filesize/1024/1024:.1f} MB" if filesize else "  📦 File Size: Unknown")
            print(f"  📝 Note: {format_note}")
            print(f"  🔗 URL: {url}")
            print()
            
        # Check for audio availability
        audio_formats = [f for f in formats if f.get('acodec', 'none') != 'none']
        video_only_formats = [f for f in formats if f.get('acodec', 'none') == 'none' and f.get('vcodec', 'none') != 'none']
        
        print("🔊 AUDIO ANALYSIS:")
        print(f"  📊 Total formats: {len(formats)}")
        print(f"  🔊 Formats with audio: {len(audio_formats)}")
        print(f"  📹 Video-only formats: {len(video_only_formats)}")
        
        if not audio_formats:
            print("  ❌ NO AUDIO FORMATS FOUND - This explains the no audio issue!")
        else:
            print("  ✅ Audio formats available:")
            for fmt in audio_formats[:3]:
                print(f"    - {fmt.get('format_id')}: {fmt.get('acodec')} ({fmt.get('resolution', 'audio-only')})")
                
        # Save detailed data for analysis
        with open('facebook_metadata_debug.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"💾 Detailed data saved to: facebook_metadata_debug.json")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_facebook_metadata_extraction() 