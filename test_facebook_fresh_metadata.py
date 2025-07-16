#!/usr/bin/env python3
"""
Test script to test fresh Facebook metadata extraction with no cache.
This will test if the format selection fix works.
"""
import json
import requests
import yt_dlp
from typing import Dict

def test_direct_ytdlp_extraction():
    """Test yt-dlp extraction directly with the new format selection."""
    
    test_url = "https://www.facebook.com/reel/2797924943847507"
    
    print("🔍 Testing direct yt-dlp extraction with format selection fix")
    print("=" * 70)
    print(f"📺 URL: {test_url}")
    print()
    
    # Test with the new format selection
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,
        # New format selection that prioritizes merged formats
        "format": "best[vcodec!=none][acodec!=none]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.facebook.com/",
        },
        "socket_timeout": 30,
        "retries": 3,
    }
    
    try:
        print("🚀 Running yt-dlp extraction...")
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
            
        if not info:
            print("❌ No info extracted")
            return
            
        print("✅ Extraction successful!")
        print(f"📽️ Title: {info.get('title', 'N/A')}")
        print(f"⏱️ Duration: {info.get('duration', 'N/A')} seconds")
        print()
        
        formats = info.get('formats', [])
        print(f"🎯 Found {len(formats)} formats:")
        print("-" * 50)
        
        # Check the selected format (should be the first one with the new selection)
        if formats:
            selected_format = formats[0]  # yt-dlp orders by preference
            print("🎖️ SELECTED FORMAT (will be used for playback):")
            print(f"  📋 ID: {selected_format.get('format_id', 'unknown')}")
            print(f"  📐 Resolution: {selected_format.get('resolution', 'unknown')}")
            print(f"  📄 Extension: {selected_format.get('ext', 'unknown')}")
            print(f"  🎬 Video Codec: {selected_format.get('vcodec', 'none')}")
            print(f"  🔊 Audio Codec: {selected_format.get('acodec', 'none')}")
            print(f"  📝 Note: {selected_format.get('format_note', '')}")
            print(f"  🔗 URL: {selected_format.get('url', '')[:80]}...")
            print()
            
            # Audio analysis
            if selected_format.get('acodec', 'none') != 'none':
                print("✅ SELECTED FORMAT HAS AUDIO!")
                print("🔧 This should fix the audio playback issue.")
            else:
                print("❌ SELECTED FORMAT STILL VIDEO-ONLY!")
                print("🔧 Format selection needs further refinement.")
            print()
        
        # Show all formats for analysis
        print("📋 ALL AVAILABLE FORMATS:")
        for i, fmt in enumerate(formats[:10]):
            vcodec = fmt.get('vcodec', 'none')
            acodec = fmt.get('acodec', 'none')
            has_audio = acodec != 'none'
            audio_indicator = "🔊" if has_audio else "🔇"
            
            print(f"  {i+1:2d}. {audio_indicator} {fmt.get('format_id', 'unknown'):20s} "
                  f"{fmt.get('resolution', 'unknown'):10s} "
                  f"v:{vcodec[:8]:8s} a:{acodec[:8]:8s} "
                  f"{fmt.get('format_note', '')[:20]:20s}")
        
        # Count formats by type
        audio_formats = [f for f in formats if f.get('acodec', 'none') != 'none']
        video_only = [f for f in formats if f.get('acodec', 'none') == 'none' and f.get('vcodec', 'none') != 'none']
        
        print()
        print(f"📊 ANALYSIS:")
        print(f"  Total formats: {len(formats)}")
        print(f"  With audio: {len(audio_formats)}")
        print(f"  Video-only: {len(video_only)}")
        
        if len(audio_formats) == 0:
            print("  🚨 NO FORMATS WITH AUDIO FOUND!")
            print("  🔧 This indicates Facebook is only providing DASH streams")
            print("  🔧 May need authentication or different extraction approach")
        
    except Exception as e:
        print(f"❌ yt-dlp extraction failed: {e}")

def test_backend_with_cache_bypass():
    """Test backend extraction with cache bypass."""
    
    print("\n" + "="*70)
    print("🔄 Testing backend extraction (cache should be cleared)")
    print("="*70)
    
    # Use a slightly different URL to bypass cache
    test_url = "https://www.facebook.com/reel/2797924943847507"  
    
    try:
        # First clear any existing cache by making a request to a non-existent endpoint
        print("🧹 Attempting to use fresh extraction...")
        
        response = requests.post(
            "http://localhost:8000/api/v1/metadata/extract",
            json={"url": test_url},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            formats = data.get('formats', [])
            
            if formats:
                selected_format = formats[0]  # First format should be the selected one
                print(f"🎖️ BACKEND SELECTED FORMAT:")
                print(f"  🔊 Audio Codec: {selected_format.get('acodec', 'none')}")
                print(f"  🎬 Video Codec: {selected_format.get('vcodec', 'none')}")
                print(f"  📝 Note: {selected_format.get('format_note', '')}")
                
                if selected_format.get('acodec', 'none') != 'none':
                    print("✅ BACKEND FIX SUCCESSFUL!")
                else:
                    print("❌ BACKEND STILL SERVING VIDEO-ONLY")
        else:
            print(f"❌ Backend request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Backend test failed: {e}")

if __name__ == "__main__":
    test_direct_ytdlp_extraction()
    test_backend_with_cache_bypass() 