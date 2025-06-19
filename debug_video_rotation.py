#!/usr/bin/env python3
"""
Video Rotation Diagnostics Script
Analyzes video rotation metadata at each stage of processing
"""

import json
import subprocess
import sys
import tempfile
import os
from pathlib import Path

def run_command(cmd, capture_output=True):
    """Run shell command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True, check=True)
        return True, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def analyze_video_metadata(video_path):
    """Extract detailed video metadata including rotation info"""
    print(f"\n🔍 ANALYZING: {video_path}")
    
    # Use ffprobe to get detailed metadata
    cmd = [
        'ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_streams',
        '-show_format',
        str(video_path)
    ]
    
    success, stdout, stderr = run_command(' '.join(cmd))
    if not success:
        print(f"❌ Failed to analyze {video_path}: {stderr}")
        return None
    
    try:
        metadata = json.loads(stdout)
        
        # Extract video stream info
        video_streams = [s for s in metadata.get('streams', []) if s.get('codec_type') == 'video']
        if not video_streams:
            print("❌ No video streams found")
            return None
        
        video_stream = video_streams[0]  # First video stream
        
        print(f"📺 Resolution: {video_stream.get('width')}x{video_stream.get('height')}")
        print(f"🎯 Codec: {video_stream.get('codec_name')}")
        
        # Check for rotation in tags
        tags = video_stream.get('tags', {})
        if 'rotate' in tags:
            print(f"🔄 Rotation tag: {tags['rotate']}°")
        
        # Check for display matrix (side data)
        side_data = video_stream.get('side_data_list', [])
        for data in side_data:
            if data.get('side_data_type') == 'Display Matrix':
                rotation = data.get('rotation', 0)
                print(f"🔄 Display Matrix rotation: {rotation}°")
        
        # Check format-level tags
        format_tags = metadata.get('format', {}).get('tags', {})
        if 'rotate' in format_tags:
            print(f"🔄 Format rotation tag: {format_tags['rotate']}°")
        
        return {
            'width': video_stream.get('width'),
            'height': video_stream.get('height'), 
            'codec': video_stream.get('codec_name'),
            'rotation_tag': tags.get('rotate'),
            'display_matrix_rotation': next(
                (data.get('rotation', 0) for data in side_data 
                 if data.get('side_data_type') == 'Display Matrix'), 
                None
            ),
            'format_rotation': format_tags.get('rotate'),
            'has_rotation': any([
                tags.get('rotate'),
                format_tags.get('rotate'),
                any(data.get('rotation') for data in side_data if data.get('side_data_type') == 'Display Matrix')
            ])
        }
        
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse metadata: {e}")
        return None

def test_existing_file(file_path):
    """Test an existing video file for rotation metadata"""
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return None
    
    return analyze_video_metadata(file_path)

def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_video_rotation.py <video_file_path>")
        print("Example: python debug_video_rotation.py /app/clips/2025-06-18/video.mp4")
        return
    
    file_path = sys.argv[1]
    
    print("🔍 VIDEO ROTATION DIAGNOSTIC TOOL")
    print("=" * 50)
    
    # Analyze the video file
    metadata = test_existing_file(file_path)
    
    if metadata:
        if metadata.get('has_rotation'):
            print(f"\n⚠️ VIDEO HAS ROTATION METADATA!")
            print("This could be causing the tilted frame issue.")
        else:
            print(f"\n✅ VIDEO APPEARS TO HAVE NO ROTATION METADATA")
            print("The rotation issue might be visual/encoding related.")
    else:
        print("❌ Could not analyze video file")

if __name__ == "__main__":
    main() 