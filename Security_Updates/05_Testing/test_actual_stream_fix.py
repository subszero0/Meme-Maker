#!/usr/bin/env python3
"""
Test what video URL is actually being served after the format selection fix.
"""
import requests
import subprocess
import tempfile
import os

def test_actual_stream_after_fix():
    """Test the actual video stream being served after format fix."""
    
    test_url = "https://www.facebook.com/reel/2797924943847507"
    
    print("🔍 Testing actual video stream after format selection fix")
    print("=" * 60)
    
    try:
        # Get metadata from backend
        response = requests.post(
            "http://localhost:8000/api/v1/metadata/extract",
            json={"url": test_url},
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ Backend request failed: {response.status_code}")
            return
            
        data = response.json()
        formats = data.get('formats', [])
        
        if not formats:
            print("❌ No formats returned")
            return
            
        # Test the first format (selected format)
        selected_format = formats[0]
        video_url = selected_format.get('url', '')
        
        print(f"🎖️ SELECTED FORMAT:")
        print(f"  📋 ID: {selected_format.get('format_id')}")
        print(f"  🔊 Audio Codec: {selected_format.get('acodec')}")
        print(f"  🎬 Video Codec: {selected_format.get('vcodec')}")
        print(f"  📝 Note: {selected_format.get('format_note')}")
        print(f"  🔗 URL: {video_url[:80]}...")
        print()
        
        # Test via backend proxy
        print("🔍 Testing via backend proxy...")
        proxy_url = f"http://localhost:8000/api/v1/video/proxy?url={requests.utils.quote(video_url)}"
        
        # Download small sample and check with ffprobe
        headers = {'Range': 'bytes=0-1048576'}  # First 1MB
        
        proxy_response = requests.get(proxy_url, headers=headers, timeout=30)
        print(f"📡 Proxy response: {proxy_response.status_code}")
        print(f"📄 Content-Type: {proxy_response.headers.get('content-type', 'unknown')}")
        
        if proxy_response.status_code == 206:
            # Save sample and analyze
            temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            temp_file.write(proxy_response.content)
            temp_file.close()
            
            print(f"💾 Sample size: {len(proxy_response.content)/1024:.1f} KB")
            
            # Check with ffprobe
            try:
                cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', temp_file.name]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    import json
                    probe_data = json.loads(result.stdout)
                    streams = probe_data.get('streams', [])
                    
                    video_streams = [s for s in streams if s.get('codec_type') == 'video']
                    audio_streams = [s for s in streams if s.get('codec_type') == 'audio']
                    
                    print(f"🎬 Video streams: {len(video_streams)}")
                    print(f"🔊 Audio streams: {len(audio_streams)}")
                    
                    if audio_streams:
                        print("✅ AUDIO STREAMS FOUND IN ACTUAL FILE!")
                        print("🎉 Format selection fix is working!")
                        for audio in audio_streams:
                            print(f"  🎵 Audio: {audio.get('codec_name')} at {audio.get('sample_rate')}Hz")
                    else:
                        print("❌ NO AUDIO STREAMS IN ACTUAL FILE")
                        print("🔧 The format selection fix needs more work")
                        print("🔧 The URL is still pointing to video-only DASH stream")
                else:
                    print(f"❌ ffprobe failed: {result.stderr}")
                    
            except FileNotFoundError:
                print("❌ ffprobe not found")
            
            # Cleanup
            os.unlink(temp_file.name)
        else:
            print(f"❌ Proxy request failed: {proxy_response.status_code}")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_actual_stream_after_fix() 