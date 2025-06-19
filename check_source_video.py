#!/usr/bin/env python3
"""
Source Video Analysis Script
Downloads and analyzes the source video before any processing
"""

import subprocess
import json
import tempfile
import os
from pathlib import Path
import yt_dlp

def analyze_source_video(url):
    """Download and analyze the source video from YouTube"""
    print("🎬 SOURCE VIDEO ANALYSIS")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "source.%(ext)s"
        
        # Same yt-dlp options as our worker
        ydl_opts = {
            'format': '22',  # Same format as in the logs
            'outtmpl': str(temp_path),
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            print(f"📥 Downloading source video...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Find the downloaded file
            downloaded_files = list(Path(temp_dir).glob("source.*"))
            if not downloaded_files:
                print("❌ No file downloaded")
                return
            
            source_file = downloaded_files[0]
            print(f"✅ Downloaded: {source_file.name} ({source_file.stat().st_size} bytes)")
            
            # Analyze with ffprobe
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-show_format',
                str(source_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            metadata = json.loads(result.stdout)
            
            # Extract video stream info
            video_streams = [s for s in metadata.get('streams', []) if s.get('codec_type') == 'video']
            if not video_streams:
                print("❌ No video streams found")
                return
            
            video_stream = video_streams[0]
            print(f"\n📺 SOURCE VIDEO PROPERTIES:")
            print(f"Resolution: {video_stream.get('width')}x{video_stream.get('height')}")
            print(f"Codec: {video_stream.get('codec_name')}")
            print(f"Duration: {float(metadata.get('format', {}).get('duration', 0)):.2f}s")
            
            # Check for rotation in tags
            tags = video_stream.get('tags', {})
            format_tags = metadata.get('format', {}).get('tags', {})
            side_data = video_stream.get('side_data_list', [])
            
            print(f"\n🔍 ROTATION ANALYSIS:")
            
            # Stream tags
            if 'rotate' in tags:
                print(f"🔄 Stream rotation tag: {tags['rotate']}°")
            
            # Format tags  
            if 'rotate' in format_tags:
                print(f"🔄 Format rotation tag: {format_tags['rotate']}°")
            
            # Display matrix
            for data in side_data:
                if data.get('side_data_type') == 'Display Matrix':
                    rotation = data.get('rotation', 0)
                    if rotation:
                        print(f"🔄 Display Matrix rotation: {rotation}°")
            
            # Check for mobile video indicators
            print(f"\n📱 MOBILE VIDEO INDICATORS:")
            handler = tags.get('handler_name', '').lower()
            encoder = tags.get('encoder', '').lower()
            
            print(f"Handler: {tags.get('handler_name', 'N/A')}")
            print(f"Encoder: {tags.get('encoder', 'N/A')}")
            
            if 'google' in handler:
                print("⚠️ Google handler detected (potential mobile source)")
            
            # Aspect ratio analysis
            width = video_stream.get('width', 0)
            height = video_stream.get('height', 0)
            if width > 0 and height > 0:
                aspect_ratio = width / height
                print(f"\n📐 ASPECT RATIO ANALYSIS:")
                print(f"Aspect ratio: {aspect_ratio:.3f}")
                if aspect_ratio < 1.0:
                    print("⚠️ Portrait orientation detected")
                elif 1.7 < aspect_ratio < 1.8:
                    print("✅ Standard 16:9 landscape")
                elif aspect_ratio > 2.0:
                    print("⚠️ Ultra-wide format")
                else:
                    print(f"📏 Custom aspect ratio: {aspect_ratio:.3f}")
            
            # Summary
            has_rotation = any([
                tags.get('rotate'),
                format_tags.get('rotate'),
                any(data.get('rotation') for data in side_data if data.get('side_data_type') == 'Display Matrix')
            ])
            
            print(f"\n🎯 CONCLUSION:")
            if has_rotation:
                print("⚠️ SOURCE VIDEO HAS ROTATION METADATA")
                print("This could be the cause of the tilted frame issue")
            else:
                print("✅ SOURCE VIDEO HAS NO ROTATION METADATA")
                print("The tilt issue is likely introduced during processing or is a visual encoding artifact")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Use the same URL from the logs
    url = "https://www.youtube.com/watch?v=TzUWcoI9TpA"
    analyze_source_video(url) 