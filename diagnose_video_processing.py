#!/usr/bin/env python3
"""
Comprehensive Video Processing Diagnostic Script
Tests the complete video processing pipeline with detailed logging
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime

def log_with_timestamp(message, prefix="🔍 DIAG"):
    """Log message with precise timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"{timestamp} {prefix}: {message}")

def run_command(cmd, timeout=60):
    """Run command with timeout and capture output"""
    try:
        log_with_timestamp(f"Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd()
        )
        return result
    except subprocess.TimeoutExpired:
        log_with_timestamp(f"Command timed out after {timeout}s", "⚠️ WARN")
        return None
    except Exception as e:
        log_with_timestamp(f"Command failed: {e}", "❌ ERROR")
        return None

def test_yt_dlp_formats():
    """Test yt-dlp format listing"""
    log_with_timestamp("=== TESTING YT-DLP FORMAT LISTING ===")
    
    url = "https://www.youtube.com/watch?v=vEy6tcU6eLU"
    
    # Test basic info extraction
    cmd = ["yt-dlp", "--list-formats", "--no-warnings", url]
    result = run_command(cmd, timeout=30)
    
    if result and result.returncode == 0:
        log_with_timestamp("✅ yt-dlp can access video")
        lines = result.stdout.strip().split('\n')
        format_count = len([line for line in lines if line.strip() and not line.startswith('[') and 'format code' not in line.lower()])
        log_with_timestamp(f"Found {format_count} formats")
        
        # Look for format 232 specifically
        format_232_found = False
        for line in lines:
            if '232' in line and 'mp4' in line:
                format_232_found = True
                log_with_timestamp(f"Found format 232: {line.strip()}")
                break
        
        if not format_232_found:
            log_with_timestamp("⚠️ Format 232 not found in available formats", "⚠️ WARN")
    else:
        log_with_timestamp("❌ yt-dlp failed to list formats", "❌ ERROR")
        if result:
            log_with_timestamp(f"Error: {result.stderr}", "❌ ERROR")
        return False
    
    return True

def test_video_download():
    """Test downloading video with format 232"""
    log_with_timestamp("=== TESTING VIDEO DOWNLOAD ===")
    
    url = "https://www.youtube.com/watch?v=vEy6tcU6eLU"
    output_file = "test_download.%(ext)s"
    
    # Download with format 232 (720p)
    cmd = [
        "yt-dlp",
        "-f", "232",
        "-o", output_file,
        "--no-warnings",
        url
    ]
    
    result = run_command(cmd, timeout=120)
    
    if result and result.returncode == 0:
        # Find the actual downloaded file
        downloaded_files = [f for f in os.listdir('.') if f.startswith('test_download')]
        if downloaded_files:
            actual_file = downloaded_files[0]
            log_with_timestamp(f"✅ Downloaded: {actual_file}")
            
            # Get file info
            file_size = os.path.getsize(actual_file)
            log_with_timestamp(f"File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
            
            return actual_file
        else:
            log_with_timestamp("❌ Download completed but no file found", "❌ ERROR")
    else:
        log_with_timestamp("❌ Download failed", "❌ ERROR")
        if result:
            log_with_timestamp(f"Error: {result.stderr}", "❌ ERROR")
    
    return None

def analyze_video_file(video_file):
    """Analyze video file with ffprobe"""
    log_with_timestamp(f"=== ANALYZING VIDEO FILE: {video_file} ===")
    
    # Get detailed video information
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        video_file
    ]
    
    result = run_command(cmd, timeout=30)
    
    if result and result.returncode == 0:
        try:
            info = json.loads(result.stdout)
            
            # Analyze format
            if 'format' in info:
                format_info = info['format']
                log_with_timestamp(f"Duration: {format_info.get('duration', 'Unknown')} seconds")
                log_with_timestamp(f"Bitrate: {format_info.get('bit_rate', 'Unknown')} bps")
                log_with_timestamp(f"Format: {format_info.get('format_name', 'Unknown')}")
            
            # Analyze streams
            video_streams = []
            audio_streams = []
            
            for stream in info.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_streams.append(stream)
                    log_with_timestamp(f"Video stream: {stream.get('codec_name')} {stream.get('width')}x{stream.get('height')} @ {stream.get('r_frame_rate', 'Unknown')} fps")
                elif stream.get('codec_type') == 'audio':
                    audio_streams.append(stream)
                    log_with_timestamp(f"Audio stream: {stream.get('codec_name')} {stream.get('sample_rate', 'Unknown')} Hz")
            
            log_with_timestamp(f"Total streams: {len(video_streams)} video, {len(audio_streams)} audio")
            return info
            
        except json.JSONDecodeError as e:
            log_with_timestamp(f"❌ Failed to parse ffprobe output: {e}", "❌ ERROR")
    else:
        log_with_timestamp("❌ ffprobe failed", "❌ ERROR")
        if result:
            log_with_timestamp(f"Error: {result.stderr}", "❌ ERROR")
    
    return None

def test_ffmpeg_trimming(video_file, start_time=4, duration=4):
    """Test FFmpeg trimming with precise timing"""
    log_with_timestamp(f"=== TESTING FFMPEG TRIMMING: {start_time}s + {duration}s ===")
    
    output_file = f"test_trim_{start_time}_{duration}.mp4"
    
    # Use the same FFmpeg command as in the worker
    cmd = [
        "ffmpeg",
        "-i", video_file,
        "-ss", str(start_time),
        "-t", str(duration),
        "-map", "0:v:0",
        "-map", "0:a:0?",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-avoid_negative_ts", "make_zero",
        "-y",
        output_file
    ]
    
    start_time_process = time.time()
    result = run_command(cmd, timeout=60)
    end_time_process = time.time()
    
    log_with_timestamp(f"FFmpeg processing took {end_time_process - start_time_process:.2f} seconds")
    
    if result and result.returncode == 0:
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            log_with_timestamp(f"✅ Trimmed video created: {output_file} ({file_size:,} bytes)")
            
            # Analyze the trimmed video
            trimmed_info = analyze_video_file(output_file)
            
            if trimmed_info and 'format' in trimmed_info:
                actual_duration = float(trimmed_info['format'].get('duration', 0))
                expected_duration = duration
                duration_diff = abs(actual_duration - expected_duration)
                
                log_with_timestamp(f"Expected duration: {expected_duration}s")
                log_with_timestamp(f"Actual duration: {actual_duration:.3f}s")
                log_with_timestamp(f"Duration difference: {duration_diff:.3f}s")
                
                if duration_diff <= 0.1:  # Within 100ms tolerance
                    log_with_timestamp("✅ Duration matches expected!")
                else:
                    log_with_timestamp(f"⚠️ Duration mismatch > 0.1s", "⚠️ WARN")
                
                # Check for video/audio streams
                video_streams = [s for s in trimmed_info.get('streams', []) if s.get('codec_type') == 'video']
                audio_streams = [s for s in trimmed_info.get('streams', []) if s.get('codec_type') == 'audio']
                
                if not video_streams:
                    log_with_timestamp("❌ NO VIDEO STREAMS in output!", "❌ ERROR")
                else:
                    log_with_timestamp(f"✅ Output has {len(video_streams)} video stream(s)")
                
                if not audio_streams:
                    log_with_timestamp("⚠️ No audio streams in output", "⚠️ WARN")
                else:
                    log_with_timestamp(f"✅ Output has {len(audio_streams)} audio stream(s)")
            
            return output_file
        else:
            log_with_timestamp("❌ FFmpeg completed but no output file found", "❌ ERROR")
    else:
        log_with_timestamp("❌ FFmpeg trimming failed", "❌ ERROR")
        if result:
            log_with_timestamp(f"FFmpeg stderr: {result.stderr}", "❌ ERROR")
    
    return None

def cleanup_test_files():
    """Clean up test files"""
    log_with_timestamp("=== CLEANING UP TEST FILES ===")
    
    test_files = [f for f in os.listdir('.') if f.startswith('test_download') or f.startswith('test_trim')]
    
    for file in test_files:
        try:
            os.remove(file)
            log_with_timestamp(f"Removed: {file}")
        except Exception as e:
            log_with_timestamp(f"Failed to remove {file}: {e}", "⚠️ WARN")

def main():
    """Run comprehensive diagnostics"""
    log_with_timestamp("Starting comprehensive video processing diagnostics")
    log_with_timestamp(f"URL: https://www.youtube.com/watch?v=vEy6tcU6eLU")
    log_with_timestamp(f"Test parameters: 4s start, 4s duration")
    log_with_timestamp("=" * 60)
    
    try:
        # Test 1: Format listing
        if not test_yt_dlp_formats():
            log_with_timestamp("❌ Format listing failed, stopping diagnostics", "❌ ERROR")
            return
        
        # Test 2: Download video
        video_file = test_video_download()
        if not video_file:
            log_with_timestamp("❌ Download failed, stopping diagnostics", "❌ ERROR")
            return
        
        # Test 3: Analyze original video
        video_info = analyze_video_file(video_file)
        if not video_info:
            log_with_timestamp("❌ Video analysis failed, stopping diagnostics", "❌ ERROR")
            cleanup_test_files()
            return
        
        # Test 4: Test FFmpeg trimming
        trimmed_file = test_ffmpeg_trimming(video_file, start_time=4, duration=4)
        if not trimmed_file:
            log_with_timestamp("❌ FFmpeg trimming failed", "❌ ERROR")
        
        # Cleanup
        cleanup_test_files()
        
        log_with_timestamp("=" * 60)
        log_with_timestamp("Diagnostics completed")
        
    except KeyboardInterrupt:
        log_with_timestamp("Diagnostics interrupted by user", "⚠️ WARN")
        cleanup_test_files()
    except Exception as e:
        log_with_timestamp(f"Unexpected error: {e}", "❌ ERROR")
        cleanup_test_files()

if __name__ == "__main__":
    main() 