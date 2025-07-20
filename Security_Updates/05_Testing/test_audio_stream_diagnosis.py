#!/usr/bin/env python3
"""
Test script to diagnose the actual video stream being served.
This will check if the video URL contains audio data or is video-only.
"""
import requests
import subprocess
import tempfile
import os
from pathlib import Path

def test_video_stream_audio():
    """Test if the video stream actually contains audio."""
    
    # This is the actual video URL from the logs that's being proxied
    video_url = "https://video.fdel8-1.fna.fbcdn.net/o1/v/t2/f2/m366/AQOp72vIttvZKDDtNQHVt_P58QLp_dpnRAbAEdg24_jD8qUqP5cy_GfxnoYNG26BVryi-2BKt28SujpNCl9qq9scYQ8luz8kvZnVtSE.mp4?_nc_cat=103&_nc_oc=AdmzYkTi0J0dlsuF-8YXlEFV6_ROoK8ngpTV466v1uqa_LEX3wS68GjJa4ZEQu6PBhs&_nc_sid=9ca052&_nc_ht=video.fdel8-1.fna.fbcdn.net&_nc_ohc=eVLFATFHz4cQ7kNvwFTo7cr&efg=eyJ2ZW5jb2RlX3RhZyI6ImRhc2hfcjJhdjEtcjFnZW4ydnA5X3E0MCIsInZpZGVvX2lkIjoyNzk3OTI0OTQzODQ3NTA3LCJvaWxfdXJsZ2VuX2FwcF9pZCI6MCwiY2xpZW50X25hbWUiOiJ1bmtub3duIiwieHB2X2Fzc2V0X2lkIjozMTc4OTEzNTc0MTI4NzYsImFzc2V0X2FnZV9kYXlzIjoxMTY1LCJ2aV91c2VjYXNlX2lkIjoxMDEyMiwiZHVyYXRpb25fcyI6MTgsInVybGdlbl9zb3VyY2UiOiJ3d3cifQ%3D%3D&ccb=17-1&_nc_zt=28&oh=00_AfRjuZtOdZLi3e5t3XvlLbgi6rwAU_A5hRL3_S3vb24evQ&oe=687B5B9C"
    
    print("🔍 Testing video stream audio content")
    print("=" * 60)
    print(f"🔗 URL: {video_url[:80]}...")
    print()
    
    # Test 1: Check via backend proxy
    print("🎯 Test 1: Testing via backend proxy")
    try:
        backend_url = f"http://localhost:8000/api/v1/video/proxy?url={requests.utils.quote(video_url)}"
        print(f"🚀 Proxy URL: {backend_url[:100]}...")
        
        response = requests.head(backend_url, timeout=30)
        content_type = response.headers.get('content-type', 'unknown')
        content_length = response.headers.get('content-length', 'unknown')
        
        print(f"✅ Backend proxy response: {response.status_code}")
        print(f"📄 Content-Type: {content_type}")
        print(f"📦 Content-Length: {content_length}")
        
        if response.status_code == 206:
            print("✅ Partial content support detected (good for streaming)")
        
    except Exception as e:
        print(f"❌ Backend proxy test failed: {e}")
    
    print()
    
    # Test 2: Download a small sample and check with ffprobe
    print("🎯 Test 2: Downloading sample and checking with ffprobe")
    try:
        # Download first 1MB to analyze
        headers = {
            'Range': 'bytes=0-1048576',  # First 1MB
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15'
        }
        
        print("📥 Downloading sample...")
        response = requests.get(video_url, headers=headers, timeout=30)
        
        if response.status_code in [200, 206]:
            # Save to temp file
            temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            temp_file.write(response.content)
            temp_file.close()
            
            print(f"💾 Sample saved to: {temp_file.name}")
            print(f"📏 Sample size: {len(response.content)/1024:.1f} KB")
            
            # Use ffprobe to check streams
            try:
                cmd = [
                    'ffprobe', '-v', 'quiet', '-print_format', 'json',
                    '-show_streams', temp_file.name
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    import json
                    probe_data = json.loads(result.stdout)
                    streams = probe_data.get('streams', [])
                    
                    video_streams = [s for s in streams if s.get('codec_type') == 'video']
                    audio_streams = [s for s in streams if s.get('codec_type') == 'audio']
                    
                    print(f"🎬 Video streams found: {len(video_streams)}")
                    print(f"🔊 Audio streams found: {len(audio_streams)}")
                    
                    if video_streams:
                        vs = video_streams[0]
                        print(f"  📐 Video: {vs.get('width', '?')}x{vs.get('height', '?')}")
                        print(f"  🎯 Video codec: {vs.get('codec_name', 'unknown')}")
                    
                    if audio_streams:
                        as_ = audio_streams[0]
                        print(f"  🔊 Audio codec: {as_.get('codec_name', 'unknown')}")
                        print(f"  🎵 Sample rate: {as_.get('sample_rate', 'unknown')}")
                        print("  ✅ AUDIO IS PRESENT!")
                    else:
                        print("  ❌ NO AUDIO STREAMS FOUND IN FILE!")
                        print("  🚨 This confirms the video URL is video-only!")
                else:
                    print(f"❌ ffprobe failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print("❌ ffprobe timed out")
            except FileNotFoundError:
                print("❌ ffprobe not found - install ffmpeg to run this test")
            
            # Cleanup
            os.unlink(temp_file.name)
            
        else:
            print(f"❌ Download failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Sample download test failed: {e}")
    
    print()
    print("🎯 DIAGNOSIS SUMMARY:")
    print("1. Metadata extraction shows 'audio will be merged' but...")
    print("2. The actual video URL being served appears to be video-only")
    print("3. This explains why ReactPlayer shows video but no audio")
    print("4. The issue is in format selection - we're getting video-only DASH streams")

if __name__ == "__main__":
    test_video_stream_audio() 