#!/usr/bin/env python3
"""
Black Border Frame Tilt Diagnostic Script

This script analyzes the video processing pipeline to identify
where the black border frame tilt is being introduced.

Hypotheses:
1. Container/viewport tilt in FFmpeg output settings
2. Encoding stage introducing systematic skew  
3. Multiple tilt sources affecting both content and container
4. Post-processing artifact after FFmpeg
"""

import subprocess
import json
import os
from pathlib import Path

def run_command(command, cwd=None):
    """Run command and return output"""
    try:
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            shell=True,
            cwd=cwd
        )
        if result.returncode != 0:
            print(f"❌ Command failed: {command}")
            print(f"Error: {result.stderr}")
            return None
        return result.stdout.strip()
    except Exception as e:
        print(f"❌ Exception running command: {e}")
        return None

def analyze_video_container_properties(video_path):
    """Analyze container and stream properties for systematic tilt"""
    print(f"\n🔍 **ANALYZING CONTAINER PROPERTIES**: {video_path}")
    
    # Get detailed container info
    cmd = f'docker exec meme-maker-backend ffprobe -v quiet -print_format json -show_format -show_streams "{video_path}"'
    output = run_command(cmd)
    
    if not output:
        return None
    
    try:
        data = json.loads(output)
        
        # Container format info
        format_info = data.get('format', {})
        print(f"📦 **Container Format**: {format_info.get('format_name', 'Unknown')}")
        print(f"📏 **Duration**: {format_info.get('duration', 'Unknown')} seconds")
        print(f"💾 **Size**: {format_info.get('size', 'Unknown')} bytes")
        
        # Stream info
        for i, stream in enumerate(data.get('streams', [])):
            if stream.get('codec_type') == 'video':
                print(f"\n📺 **Video Stream {i}**:")
                print(f"   🎥 Codec: {stream.get('codec_name', 'Unknown')}")
                print(f"   📐 Resolution: {stream.get('width', '?')}x{stream.get('height', '?')}")
                print(f"   🎨 Pixel Format: {stream.get('pix_fmt', 'Unknown')}")
                print(f"   🔄 Display Aspect Ratio: {stream.get('display_aspect_ratio', 'Unknown')}")
                print(f"   📦 Sample Aspect Ratio: {stream.get('sample_aspect_ratio', 'Unknown')}")
                
                # Check for rotation/transformation metadata
                side_data = stream.get('side_data_list', [])
                if side_data:
                    print(f"   🔄 Side Data: {side_data}")
                
                # Check disposition
                disposition = stream.get('disposition', {})
                print(f"   🏷️  Disposition: {disposition}")
                
                # Check for any field_order or interlacing
                field_order = stream.get('field_order', 'unknown')
                print(f"   🎬 Field Order: {field_order}")
                
        return data
        
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON: {e}")
        return None

def check_ffmpeg_processing_stages():
    """Check FFmpeg processing at different stages"""
    print("\n🔬 **CHECKING FFMPEG PROCESSING STAGES**")
    
    # Get recent processed videos
    storage_path = "/app/storage"
    cmd = f'docker exec meme-maker-backend find {storage_path} -name "*.mp4" -type f | head -5'
    video_files = run_command(cmd)
    
    if not video_files:
        print("❌ No processed videos found in storage")
        return
    
    video_list = video_files.strip().split('\n')
    
    for video_path in video_list[:2]:  # Analyze first 2 videos
        if video_path.strip():
            analyze_video_container_properties(video_path.strip())
            check_video_frame_properties(video_path.strip())

def check_video_frame_properties(video_path):
    """Check individual frame properties for systematic issues"""
    print(f"\n🖼️  **ANALYZING FRAME PROPERTIES**: {video_path}")
    
    # Extract first frame for analysis
    temp_frame = "/tmp/frame_analysis.png"
    cmd = f'docker exec meme-maker-backend ffmpeg -i "{video_path}" -vframes 1 -y "{temp_frame}"'
    result = run_command(cmd)
    
    if result is not None:
        # Analyze frame dimensions and properties
        cmd = f'docker exec meme-maker-backend ffprobe -v quiet -select_streams v:0 -show_entries frame=width,height,pix_fmt -of csv=p=0 "{video_path}" | head -1'
        frame_info = run_command(cmd)
        print(f"🖼️  Frame Properties: {frame_info}")
        
        # Check for any systematic pixel-level issues
        cmd = f'docker exec meme-maker-backend ffprobe -f lavfi -i "movie={video_path},signalstats" -show_entries frame=lavfi.signalstats.YAVG,lavfi.signalstats.UAVG,lavfi.signalstats.VAVG -of csv=p=0 | head -1'
        signal_stats = run_command(cmd)
        print(f"📊 Signal Stats: {signal_stats}")

def check_current_ffmpeg_command():
    """Check the current FFmpeg command being used in worker"""
    print("\n🔧 **CHECKING CURRENT FFMPEG COMMAND**")
    
    # Read current worker process_clip.py
    try:
        with open('worker/process_clip.py', 'r') as f:
            content = f.read()
            
        # Find the FFmpeg command construction
        lines = content.split('\n')
        in_ffmpeg_section = False
        
        for i, line in enumerate(lines):
            if 'ffmpeg_cmd' in line and 'output_path' in line:
                print(f"📝 **FFmpeg Command Construction** (Line {i+1}):")
                # Show context around FFmpeg command
                start = max(0, i-5)
                end = min(len(lines), i+15)
                for j in range(start, end):
                    marker = ">>> " if j == i else "    "
                    print(f"{marker}{j+1:3d}: {lines[j]}")
                break
                
    except Exception as e:
        print(f"❌ Error reading worker file: {e}")

def test_minimal_ffmpeg_reproduction():
    """Test minimal FFmpeg command to reproduce the issue"""
    print("\n🧪 **TESTING MINIMAL FFMPEG REPRODUCTION**")
    
    # Test basic FFmpeg encoding without any filters
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll as test
    
    print("Testing basic FFmpeg without any rotation filters...")
    
    # Step 1: Extract with yt-dlp
    cmd = f'docker exec meme-maker-worker yt-dlp --format "best[height<=720]" --get-url "{test_url}"'
    direct_url = run_command(cmd)
    
    if direct_url:
        print(f"✅ Got direct URL: {direct_url[:100]}...")
        
        # Step 2: Test basic FFmpeg copy (no re-encoding)
        output_copy = "/tmp/test_copy.mp4"
        cmd = f'docker exec meme-maker-worker ffmpeg -i "{direct_url}" -c copy -t 10 -y "{output_copy}"'
        result = run_command(cmd)
        
        if result is not None:
            print("✅ Basic copy completed")
            analyze_video_container_properties(output_copy)
        
        # Step 3: Test basic FFmpeg re-encode (no filters)
        output_encode = "/tmp/test_encode.mp4"
        cmd = f'docker exec meme-maker-worker ffmpeg -i "{direct_url}" -c:v libx264 -c:a aac -t 10 -y "{output_encode}"'
        result = run_command(cmd)
        
        if result is not None:
            print("✅ Basic re-encode completed")
            analyze_video_container_properties(output_encode)

def main():
    """Main diagnostic function"""
    print("🔍 **BLACK BORDER FRAME TILT DIAGNOSTIC**")
    print("=" * 50)
    
    # Check current processing
    check_current_ffmpeg_command()
    
    # Analyze existing processed videos
    check_ffmpeg_processing_stages()
    
    # Test minimal reproduction
    test_minimal_ffmpeg_reproduction()
    
    print("\n" + "=" * 50)
    print("🎯 **NEXT STEPS**:")
    print("1. Review FFmpeg command construction for container issues")
    print("2. Check if tilt exists in copy vs re-encode")
    print("3. Test different pixel formats and encoding settings")
    print("4. Analyze if issue is in player vs actual video file")

if __name__ == "__main__":
    main() 