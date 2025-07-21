#!/usr/bin/env python3
"""
Test YouTube blocking issues and verify resolution-specific downloads work.
"""

import requests
import json
import time
import sys
import subprocess
import tempfile
import os

BASE_URL = "http://localhost:8000"

# Test with multiple popular YouTube videos that often get blocked
TEST_VIDEOS = [
    {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "title": "Rick Astley - Never Gonna Give You Up",
        "description": "Classic Rick Roll video"
    },
    {
        "url": "https://www.youtube.com/watch?v=kJQP7kiw5Fk", 
        "title": "Luis Fonsi - Despacito",
        "description": "Popular music video"
    },
    {
        "url": "https://www.youtube.com/watch?v=fJ9rUzIMcZQ",
        "title": "Queen - Bohemian Rhapsody",
        "description": "Popular music video"
    },
    {
        "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
        "title": "Me at the zoo",
        "description": "First YouTube video (usually works)"
    }
]

def test_metadata_extraction(video):
    """Test if we can extract metadata for a video"""
    print(f"\n🔍 Testing metadata extraction for: {video['title']}")
    print(f"   URL: {video['url']}")
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/metadata/extract", 
                               json={"url": video['url']}, 
                               timeout=45)
        
        if response.status_code != 200:
            print(f"❌ Metadata extraction failed: {response.status_code}")
            if response.text:
                print(f"   📋 Error: {response.text[:200]}")
            return None
        
        data = response.json()
        formats = data.get('formats', [])
        
        if not formats:
            print("❌ No formats found")
            return None
        
        print(f"✅ Success! Found {len(formats)} formats")
        
        # Show available formats
        print("📋 Available formats:")
        for i, fmt in enumerate(formats[:8]):  # Show first 8 formats
            resolution = fmt['resolution']
            format_id = fmt['format_id']
            filesize = fmt.get('filesize')
            size_str = f"({filesize // 1024 // 1024:.1f}MB)" if filesize else "(unknown size)"
            print(f"   {i+1}. {format_id} - {resolution} {size_str}")
        
        return formats
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def analyze_video_file(file_path):
    """Analyze downloaded video file"""
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
            'resolution': f"{video_streams[0].get('width')}x{video_streams[0].get('height')}" if video_streams else None,
            'video_codec': video_streams[0].get('codec_name') if video_streams else None,
            'audio_codec': audio_streams[0].get('codec_name') if audio_streams else None,
        }
        
    except Exception as e:
        return {'error': str(e)}

def test_video_download(url, format_id, format_description, test_name):
    """Test downloading a specific format and return analysis"""
    print(f"\n🎬 {test_name}: Testing format {format_id} ({format_description})")
    
    try:
        # Create job
        job_data = {
            "url": url,
            "in_ts": 10.0,
            "out_ts": 15.0,  # 5-second clip
            "format_id": format_id
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/jobs", json=job_data, timeout=30)
        if response.status_code != 201:
            print(f"❌ Job creation failed: {response.status_code}")
            return None
        
        job_id = response.json()['id']
        print(f"✅ Job created: {job_id}")
        
        # Monitor job
        max_wait = 180  # 3 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_response = requests.get(f"{BASE_URL}/api/v1/jobs/{job_id}", timeout=10)
            if status_response.status_code != 200:
                print(f"❌ Status check failed")
                return None
            
            job_status = status_response.json()
            status = job_status['status']
            progress = job_status.get('progress', 0)
            stage = job_status.get('stage', 'unknown')
            
            print(f"📊 Status: {status} | Progress: {progress}% | Stage: {stage}")
            
            if status == 'done':
                download_url = job_status.get('download_url')
                if not download_url:
                    print("❌ No download URL")
                    return None
                
                # Download and analyze
                try:
                    video_response = requests.get(download_url, timeout=30)
                    if video_response.status_code != 200:
                        print(f"❌ Download failed: {video_response.status_code}")
                        return None
                    
                    # Save to temp file and analyze
                    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                        temp_file.write(video_response.content)
                        temp_path = temp_file.name
                    
                    try:
                        file_size = len(video_response.content)
                        analysis = analyze_video_file(temp_path)
                        
                        if 'error' in analysis:
                            print(f"❌ Video analysis failed: {analysis['error']}")
                            return None
                        
                        result = {
                            'format_id': format_id,
                            'format_description': format_description,
                            'file_size': file_size,
                            'analysis': analysis,
                            'download_url': download_url
                        }
                        
                        print(f"✅ SUCCESS!")
                        print(f"   📁 File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
                        print(f"   🎬 Resolution: {analysis['resolution']}")
                        print(f"   ⏱️  Duration: {analysis['duration']:.1f}s")
                        print(f"   📺 Video streams: {analysis['video_streams']}")
                        print(f"   🔊 Audio streams: {analysis['audio_streams']}")
                        
                        return result
                        
                    finally:
                        os.unlink(temp_path)
                        
                except Exception as e:
                    print(f"❌ Download/analysis error: {e}")
                    return None
                    
            elif status == 'error':
                error_code = job_status.get('error_code', 'unknown')
                print(f"❌ Job failed: {error_code}")
                return None
            
            time.sleep(3)
        
        print(f"⏰ Timeout after {max_wait} seconds")
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_resolution_comparison(video_info):
    """Test downloading the same video in different resolutions"""
    print(f"\n🎯 RESOLUTION COMPARISON TEST")
    print(f"Video: {video_info['title']}")
    print("=" * 60)
    
    url = video_info['url']
    
    # Get formats
    formats = test_metadata_extraction(video_info)
    if not formats:
        print("❌ Cannot get formats for comparison test")
        return False
    
    # Select 2-3 different formats for comparison
    test_formats = []
    
    # Try to get high, medium, and low quality formats
    for fmt in formats:
        resolution = fmt['resolution']
        format_id = fmt['format_id']
        
        # High quality (1080p+)
        if ('1080' in resolution or '1440' in resolution or '2160' in resolution) and len(test_formats) == 0:
            test_formats.append((format_id, resolution, "High Quality"))
        # Medium quality (720p, 480p)
        elif ('720' in resolution or '480' in resolution) and len([f for f in test_formats if "Medium" in f[2]]) == 0:
            test_formats.append((format_id, resolution, "Medium Quality"))
        # Low quality (360p, 240p)
        elif ('360' in resolution or '240' in resolution or '144' in resolution) and len([f for f in test_formats if "Low" in f[2]]) == 0:
            test_formats.append((format_id, resolution, "Low Quality"))
    
    # Limit to 3 formats max to avoid long test times
    test_formats = test_formats[:3]
    
    if len(test_formats) < 2:
        print("⚠️  Not enough different formats available for comparison")
        # Use first 2 available formats
        test_formats = [(f['format_id'], f['resolution'], f"Quality {i+1}") for i, f in enumerate(formats[:2])]
    
    print(f"\n🎬 Testing {len(test_formats)} different resolutions:")
    for format_id, resolution, quality in test_formats:
        print(f"   - {quality}: {format_id} ({resolution})")
    
    # Download each format
    results = []
    for i, (format_id, resolution, quality) in enumerate(test_formats):
        result = test_video_download(url, format_id, f"{resolution} - {quality}", f"Test {i+1}")
        if result:
            results.append(result)
        
        # Small delay between downloads
        if i < len(test_formats) - 1:
            print("⏳ Waiting 5 seconds before next download...")
            time.sleep(5)
    
    # Analyze results
    print(f"\n📊 COMPARISON RESULTS")
    print("=" * 60)
    
    if len(results) < 2:
        print("❌ Not enough successful downloads for comparison")
        return False
    
    # Sort by file size (descending)
    results.sort(key=lambda x: x['file_size'], reverse=True)
    
    print("File size comparison (largest to smallest):")
    for i, result in enumerate(results):
        size_mb = result['file_size'] / 1024 / 1024
        resolution = result['analysis']['resolution']
        print(f"   {i+1}. {result['format_description']}: {size_mb:.2f} MB ({resolution})")
    
    # Check if there are meaningful differences
    largest = results[0]['file_size']
    smallest = results[-1]['file_size']
    ratio = largest / smallest if smallest > 0 else 1
    
    print(f"\n📈 Size ratio (largest/smallest): {ratio:.2f}x")
    
    if ratio > 1.3:  # At least 30% difference
        print("✅ SUCCESS: Different resolutions produce different file sizes!")
        print("✅ YouTube blocking issue appears to be RESOLVED!")
        print("✅ Resolution picker is working correctly!")
        return True
    else:
        print("⚠️  WARNING: File sizes are too similar")
        print("💡 This might indicate all videos are being processed at same resolution")
        return False

def main():
    print("🧪 YouTube Blocking & Resolution Test")
    print("=" * 60)
    print("This test checks if YouTube blocking is resolved and tests different resolutions.")
    print()
    
    # Check backend
    try:
        requests.get(f"{BASE_URL}/health", timeout=5)
        print("✅ Backend is running")
    except:
        print("❌ Backend not running!")
        print("💡 Start services: docker-compose up")
        return 1
    
    # Test each video to find one that works
    working_video = None
    print("\n🔍 Testing videos to find one that works...")
    
    for video in TEST_VIDEOS:
        formats = test_metadata_extraction(video)
        if formats and len(formats) >= 2:  # Need at least 2 formats for comparison
            working_video = video
            print(f"✅ Found working video: {video['title']}")
            break
        elif formats:
            print(f"⚠️  {video['title']}: Only {len(formats)} format(s) available")
        else:
            print(f"❌ {video['title']}: Failed to get formats")
    
    if not working_video:
        print("\n❌ No working videos found!")
        print("💡 YouTube blocking may still be an issue")
        print("💡 Try running: python update_ytdlp_comprehensive.py")
        return 1
    
    # Perform resolution comparison test
    success = test_resolution_comparison(working_video)
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ YouTube blocking issue RESOLVED")
        print("✅ Resolution picker working correctly")
        print("✅ Different resolutions produce different file sizes")
        print("\n🎯 Your meme maker app is fully functional!")
    else:
        print("⚠️  TESTS HAD ISSUES")
        print("💡 YouTube blocking may still exist for some videos")
        print("💡 Check Docker logs: docker-compose logs worker")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 