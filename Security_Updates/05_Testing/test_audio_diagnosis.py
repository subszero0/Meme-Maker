#!/usr/bin/env python3
"""
Diagnostic script to test audio extraction for Instagram vs Facebook videos.
Following BP #1 (Establish Ground Truth) and BP #2 (Layered Diagnosis)
"""

import json
import sys
import subprocess
from pathlib import Path

def test_video_extraction(url: str, platform: str):
    """Test yt-dlp extraction for a given URL"""
    print(f"\n{'='*60}")
    print(f"Testing {platform} URL: {url}")
    print(f"{'='*60}")
    
    # Test 1: Basic info extraction
    print("\n🔍 Step 1: Basic info extraction")
    try:
        result = subprocess.run([
            "yt-dlp", 
            "--print-json",
            "--skip-download",
            url
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            print(f"✅ Title: {data.get('title', 'N/A')}")
            print(f"✅ Duration: {data.get('duration', 'N/A')} seconds")
            print(f"✅ Uploader: {data.get('uploader', 'N/A')}")
            
            # Analyze formats
            formats = data.get('formats', [])
            print(f"✅ Total formats available: {len(formats)}")
            
            # Check for audio-only formats
            audio_formats = [f for f in formats if f.get('vcodec') == 'none' and f.get('acodec') != 'none']
            print(f"📊 Audio-only formats: {len(audio_formats)}")
            
            # Check for video formats with audio
            video_with_audio = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
            print(f"📊 Video formats with audio: {len(video_with_audio)}")
            
            # Check for video-only formats (no audio)
            video_only = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') == 'none']
            print(f"📊 Video-only formats (no audio): {len(video_only)}")
            
            # Show the first few formats with details
            print("\n📋 First 3 formats (audio analysis):")
            for i, fmt in enumerate(formats[:3]):
                print(f"Format {i+1}:")
                print(f"  - Format ID: {fmt.get('format_id', 'N/A')}")
                print(f"  - Extension: {fmt.get('ext', 'N/A')}")
                print(f"  - Video codec: {fmt.get('vcodec', 'N/A')}")
                print(f"  - Audio codec: {fmt.get('acodec', 'N/A')}")
                print(f"  - Quality: {fmt.get('format_note', 'N/A')}")
                print(f"  - URL domain: {fmt.get('url', '')[:50]}...")
                print()
                
        else:
            print(f"❌ Failed to extract info: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("❌ Extraction timed out after 30 seconds")
    except Exception as e:
        print(f"❌ Extraction error: {e}")

def main():
    """Main diagnostic function"""
    print("🎵 Audio Diagnosis Tool for Instagram vs Facebook")
    print("Following Best Practices for systematic debugging")
    
    # Test URLs - replace with actual test URLs
    test_cases = [
        {
            "platform": "Instagram", 
            "url": "https://www.instagram.com/reel/C-test-reel/"  # Replace with actual URL
        },
        {
            "platform": "Facebook",
            "url": "https://www.facebook.com/watch?v=test-video"  # Replace with actual URL  
        }
    ]
    
    print("\n📋 Test URLs provided by user:")
    for case in test_cases:
        print(f"- {case['platform']}: Please provide a real {case['platform']} URL")
    
    print("\n⚠️  Please replace the test URLs above with real URLs and run:")
    print("python test_audio_diagnosis.py")
    
    # For now, show the analysis structure
    print("\n🔬 This script will analyze:")
    print("1. Total formats available for each platform")
    print("2. Audio-only formats count")
    print("3. Video+audio formats count")  
    print("4. Video-only (no audio) formats count")
    print("5. Audio codec information")
    print("6. URL domain patterns")
    
    print("\n📝 Next steps:")
    print("1. Provide real test URLs for both platforms")
    print("2. Run this script to compare audio extraction")
    print("3. Test the URLs in the application")
    print("4. Compare browser network requests")

if __name__ == "__main__":
    main() 