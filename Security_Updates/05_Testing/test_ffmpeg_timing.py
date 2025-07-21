#!/usr/bin/env python3
"""
Test FFmpeg timing precision and diagnose video duration issues.
This script tests the exact same FFmpeg commands the worker uses.
"""

import subprocess
import json
import tempfile
import os
import time
from pathlib import Path

def analyze_video(file_path):
    """Analyze video file and return duration, streams info"""
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams',
            '-show_format',
            str(file_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        info = json.loads(result.stdout)
        
        video_streams = [s for s in info.get('streams', []) if s.get('codec_type') == 'video']
        audio_streams = [s for s in info.get('streams', []) if s.get('codec_type') == 'audio']
        format_info = info.get('format', {})
        
        return {
            'video_streams': len(video_streams),
            'audio_streams': len(audio_streams),
            'video_duration': float(video_streams[0].get('duration', 0)) if video_streams else 0,
            'format_duration': float(format_info.get('duration', 0)),
            'resolution': f"{video_streams[0].get('width')}x{video_streams[0].get('height')}" if video_streams else None,
            'video_codec': video_streams[0].get('codec_name') if video_streams else None,
            'audio_codec': audio_streams[0].get('codec_name') if audio_streams else None,
            'file_size': os.path.getsize(file_path),
        }
        
    except Exception as e:
        return {'error': str(e)}

def test_docker_ffmpeg():
    """Test FFmpeg timing inside Docker worker container"""
    print("🐳 Testing FFmpeg in Docker worker container...")
    
    # Test parameters matching user's issue
    in_ts = 4.0
    out_ts = 12.0
    expected_duration = out_ts - in_ts  # 8 seconds
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    
    print(f"   - Test URL: {test_url}")
    print(f"   - Start time: {in_ts}s")
    print(f"   - End time: {out_ts}s")
    print(f"   - Expected duration: {expected_duration}s")
    
    # Test inside worker container
    test_cmd = f'''
import subprocess
import json
import tempfile
from pathlib import Path

# Step 1: Download video
print("📥 Downloading test video...")
import yt_dlp

with tempfile.TemporaryDirectory() as temp_dir:
    temp_path = Path(temp_dir)
    source_file = temp_path / "test.%(ext)s"
    
    ydl_opts = {{
        'outtmpl': str(source_file),
        'format': 'best[height<=720]/best',
        'quiet': True,
        'no_warnings': True,
    }}
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(["{test_url}"])
    
    # Find downloaded file
    downloaded = list(temp_path.glob("test.*"))
    if not downloaded:
        print("❌ Download failed")
        exit(1)
    
    source = downloaded[0]
    print(f"✅ Downloaded: {{source}} ({{source.stat().st_size:,}} bytes)")
    
    # Analyze source
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', '-show_format', str(source)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    info = json.loads(result.stdout)
    
    video_streams = [s for s in info.get('streams', []) if s.get('codec_type') == 'video']
    if video_streams:
        vs = video_streams[0]
        print(f"📊 Source: {{vs.get('width')}}x{{vs.get('height')}}, {{float(vs.get('duration', 0)):.3f}}s")
    
    # Test Method 1: -ss + -to (current method)
    print("\\n🎬 Method 1: -ss + -to")
    output1 = temp_path / "output1.mp4"
    cmd1 = [
        'ffmpeg', '-i', str(source),
        '-ss', '{in_ts}', '-to', '{out_ts}',
        '-c:v', 'copy', '-c:a', 'copy',
        '-map', '0:v:0', '-map', '0:a:0?',
        '-avoid_negative_ts', 'make_zero',
        str(output1), '-y'
    ]
    result1 = subprocess.run(cmd1, capture_output=True, text=True)
    
    if result1.returncode == 0 and output1.exists():
        # Analyze output
        cmd_probe = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', str(output1)]
        probe_result = subprocess.run(cmd_probe, capture_output=True, text=True, check=True)
        output_info = json.loads(probe_result.stdout)
        
        video_streams = [s for s in output_info.get('streams', []) if s.get('codec_type') == 'video']
        if video_streams:
            actual_duration = float(video_streams[0].get('duration', 0))
            file_size = output1.stat().st_size
            print(f"   ✅ Duration: {{actual_duration:.3f}}s (expected: {expected_duration}s)")
            print(f"   📁 Size: {{file_size:,}} bytes")
            print(f"   🎯 Difference: {{abs(actual_duration - {expected_duration}):.3f}}s")
        else:
            print("   ❌ No video streams in output")
    else:
        print(f"   ❌ Failed: {{result1.stderr}}")
    
    # Test Method 2: -ss + -t (duration)
    print("\\n🎬 Method 2: -ss + -t")
    output2 = temp_path / "output2.mp4"
    cmd2 = [
        'ffmpeg', '-i', str(source),
        '-ss', '{in_ts}', '-t', '{expected_duration}',
        '-c:v', 'copy', '-c:a', 'copy',
        '-map', '0:v:0', '-map', '0:a:0?',
        '-avoid_negative_ts', 'make_zero',
        str(output2), '-y'
    ]
    result2 = subprocess.run(cmd2, capture_output=True, text=True)
    
    if result2.returncode == 0 and output2.exists():
        cmd_probe = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', str(output2)]
        probe_result = subprocess.run(cmd_probe, capture_output=True, text=True, check=True)
        output_info = json.loads(probe_result.stdout)
        
        video_streams = [s for s in output_info.get('streams', []) if s.get('codec_type') == 'video']
        if video_streams:
            actual_duration = float(video_streams[0].get('duration', 0))
            file_size = output2.stat().st_size
            print(f"   ✅ Duration: {{actual_duration:.3f}}s (expected: {expected_duration}s)")
            print(f"   📁 Size: {{file_size:,}} bytes")
            print(f"   🎯 Difference: {{abs(actual_duration - {expected_duration}):.3f}}s")
        else:
            print("   ❌ No video streams in output")
    else:
        print(f"   ❌ Failed: {{result2.stderr}}")
    
    print("\\n🎉 Docker FFmpeg test completed!")
'''
    
    try:
        # Run test inside worker container
        docker_cmd = [
            'docker-compose', 'exec', '-T', 'worker',
            'python', '-c', test_cmd
        ]
        
        print("   Running test in worker container...")
        result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Docker test completed successfully:")
            print(result.stdout)
            return True
        else:
            print(f"❌ Docker test failed:")
            print(f"   stdout: {result.stdout}")
            print(f"   stderr: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Docker test timed out")
        return False
    except Exception as e:
        print(f"❌ Docker test error: {e}")
        return False

def main():
    print("🔧 FFmpeg Timing Diagnostic Tool")
    print("=" * 50)
    print("Testing FFmpeg timing precision to fix video duration issues.")
    print()
    
    # Check Docker
    try:
        result = subprocess.run(['docker-compose', 'ps'], capture_output=True, text=True)
        if 'worker' not in result.stdout:
            print("❌ Docker worker container not running!")
            print("💡 Start with: docker-compose up -d")
            return 1
        print("✅ Docker containers are running")
    except:
        print("❌ Docker not available!")
        return 1
    
    # Run Docker test
    success = test_docker_ffmpeg()
    
    if success:
        print("\n🎉 DIAGNOSTIC COMPLETE!")
        print("Check the results above to identify the timing issue.")
        print("The method with the smallest duration difference should be used.")
    else:
        print("\n❌ DIAGNOSTIC FAILED!")
        print("Check Docker logs: docker-compose logs worker")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main()) 