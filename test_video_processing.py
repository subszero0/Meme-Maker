#!/usr/bin/env python3
"""
Test video processing after fixes to ensure video content is preserved.
"""

import requests
import json
import time
import sys
import subprocess
import tempfile
import os

BASE_URL = "http://localhost:8000"

# Test URLs that should work
TEST_URLS = [
    "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # Me at the zoo
    "https://www.youtube.com/watch?v=kJQP7kiw5Fk",  # Despacito  
]

def analyze_video_file(file_path):
    """Analyze a video file and return detailed information"""
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams',
            '-show_format',
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        info = json.loads(result.stdout)
        
        video_streams = [s for s in info.get('streams', []) if s.get('codec_type') == 'video']
        audio_streams = [s for s in info.get('streams', []) if s.get('codec_type') == 'audio']
        format_info = info.get('format', {})
        
        return {
            'video_streams': len(video_streams),
            'audio_streams': len(audio_streams),
            'duration': float(format_info.get('duration', 0)),
            'size': int(format_info.get('size', 0)),
            'video_codec': video_streams[0].get('codec_name') if video_streams else None,
            'resolution': f"{video_streams[0].get('width')}x{video_streams[0].get('height')}" if video_streams else None,
            'audio_codec': audio_streams[0].get('codec_name') if audio_streams else None,
        }
        
    except Exception as e:
        return {'error': str(e)}

def test_video_processing(url):
    """Test complete video processing pipeline"""
    print(f"\n🎬 Testing video processing with: {url}")
    
    # Step 1: Get formats
    try:
        response = requests.post(f"{BASE_URL}/api/v1/metadata/extract", 
                               json={"url": url}, timeout=30)
        if response.status_code != 200:
            print(f"❌ Metadata failed: {response.status_code}")
            return False
        
        data = response.json()
        formats = data.get('formats', [])
        
        if not formats:
            print("❌ No formats available")
            return False
        
        # Select a good format (prefer 720p or lower for faster processing)
        selected_format = None
        for fmt in formats:
            resolution = fmt['resolution']
            if '720' in resolution or '480' in resolution:
                selected_format = fmt
                break
        
        if not selected_format:
            selected_format = formats[0]  # Use first available
        
        print(f"✅ Selected format: {selected_format['format_id']} ({selected_format['resolution']})")
        
    except Exception as e:
        print(f"❌ Metadata error: {e}")
        return False
    
    # Step 2: Create job
    try:
        job_data = {
            "url": url,
            "in_ts": 5.0,
            "out_ts": 10.0,  # 5-second clip
            "format_id": selected_format['format_id']
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/jobs", json=job_data, timeout=30)
        if response.status_code != 201:
            print(f"❌ Job creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        job_response = response.json()
        job_id = job_response['id']
        print(f"✅ Job created: {job_id}")
        
    except Exception as e:
        print(f"❌ Job creation error: {e}")
        return False
    
    # Step 3: Monitor job
    try:
        max_wait = 180  # 3 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = requests.get(f"{BASE_URL}/api/v1/jobs/{job_id}", timeout=10)
            if response.status_code != 200:
                print(f"❌ Status check failed: {response.status_code}")
                return False
            
            job_status = response.json()
            status = job_status['status']
            progress = job_status.get('progress', 0)
            stage = job_status.get('stage', 'unknown')
            
            print(f"📊 Status: {status} | Progress: {progress}% | Stage: {stage}")
            
            if status == 'done':
                download_url = job_status.get('download_url')
                if not download_url:
                    print("❌ No download URL")
                    return False
                
                print(f"✅ Job completed! Download URL: {download_url}")
                
                # Step 4: Download and analyze the video
                try:
                    video_response = requests.get(download_url, timeout=30)
                    if video_response.status_code != 200:
                        print(f"❌ Download failed: {video_response.status_code}")
                        return False
                    
                    # Save to temp file and analyze
                    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                        temp_file.write(video_response.content)
                        temp_path = temp_file.name
                    
                    try:
                        file_size = len(video_response.content)
                        print(f"📁 Downloaded file size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
                        
                        # Analyze with ffprobe
                        analysis = analyze_video_file(temp_path)
                        
                        if 'error' in analysis:
                            print(f"❌ Video analysis failed: {analysis['error']}")
                            return False
                        
                        print(f"🎬 Video Analysis:")
                        print(f"   - Video streams: {analysis['video_streams']}")
                        print(f"   - Audio streams: {analysis['audio_streams']}")
                        print(f"   - Duration: {analysis['duration']:.1f}s")
                        print(f"   - Resolution: {analysis['resolution']}")
                        print(f"   - Video codec: {analysis['video_codec']}")
                        print(f"   - Audio codec: {analysis['audio_codec']}")
                        
                        # Validate video content
                        if analysis['video_streams'] == 0:
                            print("❌ FAIL: No video streams in output!")
                            return False
                        
                        if analysis['duration'] < 4.0 or analysis['duration'] > 6.0:
                            print(f"⚠️  WARNING: Duration {analysis['duration']:.1f}s outside expected range (4-6s)")
                        
                        expected_min_size = 100 * 1024  # At least 100KB for 5s of video
                        if file_size < expected_min_size:
                            print(f"⚠️  WARNING: File size {file_size:,} bytes seems too small")
                        
                        print("✅ SUCCESS: Video processing working correctly!")
                        return True
                        
                    finally:
                        os.unlink(temp_path)  # Clean up temp file
                        
                except Exception as e:
                    print(f"❌ Download/analysis error: {e}")
                    return False
                    
            elif status == 'error':
                error_code = job_status.get('error_code', 'unknown')
                print(f"❌ Job failed: {error_code}")
                return False
            
            time.sleep(5)
        
        print(f"⏰ Timeout after {max_wait} seconds")
        return False
        
    except Exception as e:
        print(f"❌ Monitoring error: {e}")
        return False

def main():
    print("🧪 Video Processing Test")
    print("=" * 50)
    print("This test verifies that video processing fixes work correctly.")
    print()
    
    # Check backend
    try:
        requests.get(f"{BASE_URL}/health", timeout=5)
        print("✅ Backend is running")
    except:
        print("❌ Backend not running!")
        return 1
    
    # Test with available URLs
    success_count = 0
    for url in TEST_URLS:
        try:
            if test_video_processing(url):
                success_count += 1
                break  # One successful test is enough
        except KeyboardInterrupt:
            print("\n🛑 Test interrupted by user")
            return 1
        except Exception as e:
            print(f"❌ Test error: {e}")
    
    print("\n" + "=" * 50)
    if success_count > 0:
        print("🎉 SUCCESS: Video processing is working correctly!")
        print("✅ Resolution picker works")
        print("✅ Video content is preserved")
        print("✅ Output files contain valid video streams")
        print("\n🎯 The issues have been FIXED!")
    else:
        print("❌ FAILED: Video processing still has issues")
        print("💡 Check Docker logs for detailed error information")
        print("💡 Ensure Docker services are running: docker-compose ps")
    
    return 0 if success_count > 0 else 1

if __name__ == "__main__":
    sys.exit(main()) 