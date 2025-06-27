import os
import sys
import subprocess
import tempfile
import logging
import time
import shutil
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional
import json
import re

import yt_dlp
import aiofiles

# Import from backend app
sys.path.append('/app/backend')
from app import settings
from app.models import JobStatus
from app.storage_factory import get_storage_manager

# Redis will be passed as parameter from main worker
worker_redis = None
# Simplified metrics - avoid Prometheus import issues in worker
# from app.metrics import clip_job_latency_seconds, clip_jobs_inflight

logger = logging.getLogger(__name__)


def update_job_progress(job_id: str, progress: int, status: Optional[str] = None, stage: Optional[str] = None):
    """Update job progress and status in Redis"""
    try:
        if not worker_redis:
            logger.warning(f"⚠️ Redis not available, cannot update job {job_id} progress")
            return
            
        job_key = f"job:{job_id}"
        update_data = {"progress": str(progress)}  # Convert to string
        if status:
            update_data["status"] = str(status)  # Convert to string
        if stage:
            update_data["stage"] = str(stage)  # Add processing stage
        worker_redis.hset(job_key, mapping=update_data)
        worker_redis.expire(job_key, 3600)  # 1 hour expiry
        stage_msg = f" - {stage}" if stage else ""
        logger.info(f"📊 Job {job_id} progress: {progress}% {f'({status})' if status else ''}{stage_msg}")
    except Exception as e:
        logger.error(f"❌ Failed to update job progress for {job_id}: {e}")


def update_job_error(job_id: str, error_code: str, error_message: str):
    """Update job with error status and details"""
    try:
        if not worker_redis:
            logger.warning(f"⚠️ Redis not available, cannot update job {job_id} error")
            return
            
        job_key = f"job:{job_id}"
        # Convert all values to strings to avoid Redis type errors
        mapping_data = {
            "status": str(JobStatus.error.value),
            "error_code": str(error_code),
            "error_message": str(error_message[:500]),  # Truncate long error messages
            "progress": "0"  # Use "0" instead of null for error state
        }
        worker_redis.hset(job_key, mapping=mapping_data)
        worker_redis.expire(job_key, 3600)
        logger.info(f"✅ Updated job {job_id} with error status: {error_code}")
    except Exception as e:
        logger.error(f"❌ Failed to update job error for {job_id}: {e}")


def find_nearest_keyframe(video_path: str, timestamp: float) -> float:
    """Find the nearest keyframe before or at the given timestamp"""
    try:
        cmd = [
            settings.ffmpeg_path.replace('/usr/local/bin/ffmpeg', '/usr/bin/ffprobe'),
            '-v', 'quiet',
            '-select_streams', 'v:0',
            '-show_entries', 'frame=pkt_pts_time,key_frame',
            '-of', 'csv=print_section=0',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        keyframes = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split(',')
                if len(parts) >= 2 and parts[1] == '1':  # key_frame=1
                    try:
                        keyframe_time = float(parts[0])
                        if keyframe_time <= timestamp:
                            keyframes.append(keyframe_time)
                    except ValueError:
                        continue
        
        return max(keyframes) if keyframes else 0.0
        
    except Exception as e:
        logger.warning(f"Failed to find keyframe, using original timestamp: {e}")
        return timestamp


def detect_video_rotation(video_path: Path) -> Optional[str]:
    """
    Detect if video has rotation metadata or visual rotation that needs correction.
    Returns FFmpeg filter string if rotation correction is needed, None otherwise.
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams',
            str(video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        metadata = json.loads(result.stdout)
        
        for stream in metadata.get('streams', []):
            if stream.get('codec_type') == 'video':
                width = stream.get('width', 0)
                height = stream.get('height', 0)
                
                # Check for rotation in side data (Display Matrix)
                side_data = stream.get('side_data_list', [])
                for data in side_data:
                    if data.get('side_data_type') == 'Display Matrix':
                        rotation = data.get('rotation', 0)
                        if rotation:
                            logger.info(f"Found rotation metadata in Display Matrix: {rotation}°")
                            # Convert rotation to appropriate transpose filter
                            if rotation == 90 or rotation == -270:
                                return 'transpose=2'  # 90° counterclockwise
                            elif rotation == -90 or rotation == 270:
                                return 'transpose=1'  # 90° clockwise
                            elif rotation == 180 or rotation == -180:
                                return 'transpose=1,transpose=1'  # 180°
                
                # Check for rotation in stream tags
                tags = stream.get('tags', {})
                if 'rotate' in tags:
                    rotation = int(tags['rotate'])
                    logger.info(f"Found rotation tag: {rotation}°")
                    if rotation == 90:
                        return 'transpose=2'  # 90° counterclockwise  
                    elif rotation == -90 or rotation == 270:
                        return 'transpose=1'  # 90° clockwise
                    elif rotation == 180:
                        return 'transpose=1,transpose=1'  # 180°
                
                # ENHANCED: Check for visual rotation based on aspect ratio and encoding patterns
                # If video is portrait (height > width) but appears rotated from mobile source
                if height > width and width > 0 and height > 0:
                    aspect_ratio = height / width
                    
                    # Check if this looks like a rotated landscape video
                    # Common mobile video resolutions when rotated incorrectly:
                    # 360x640 (should be 640x360), 480x854 (should be 854x480), etc.
                    if aspect_ratio > 1.5:  # Very tall aspect ratio suggests rotation issue
                        # Check encoding signature for mobile/YouTube sources that often have rotation issues
                        encoder = tags.get('encoder', '').lower()
                        handler = tags.get('handler_name', '').lower()
                        
                                        # YouTube and mobile encoders often have slight visual tilt issues
                if ('google' in handler or 'youtube' in handler):
                    logger.info(f"Detected Google/YouTube video with potential tilt: {width}x{height} from {handler}")
                    # Apply small counter-clockwise rotation to fix typical clockwise camera tilt
                    # This addresses the visual tilt issue reported by users
                    logger.info("Applying 1° counter-clockwise tilt correction for YouTube video")
                    return 'rotate=-1*PI/180:fillcolor=black'  # -1° to fix clockwise tilt
                elif ('android' in handler or 'lavc' in encoder or 'x264' in encoder):
                    # For other mobile sources, only apply transpose for true portrait videos
                    if height > width and aspect_ratio > 1.5:
                        logger.info(f"Detected mobile portrait content: {width}x{height} from {handler}")
                        logger.info("Applying 90° counter-clockwise correction for mobile portrait")
                        return 'transpose=2'  # 90° counter-clockwise for true portrait
                
                # No rotation correction needed
                logger.info(f"No rotation correction needed for {width}x{height} video")
                return None
        
    except Exception as e:
        logger.warning(f"Failed to detect rotation: {e}")
        return None


def sanitize_filename(title: str, max_length: int = 100) -> str:
    """
    Sanitize a video title for use as a filename.
    Removes/replaces problematic characters and limits length.
    """
    if not title or title.strip() == '':
        return 'video'
    
    # Remove or replace problematic characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', title)  # Replace invalid filename chars
    sanitized = re.sub(r'[^\w\s\-_\.\(\)\[\]]', '', sanitized)  # Keep only safe chars
    sanitized = re.sub(r'\s+', '_', sanitized)  # Replace spaces with underscores
    sanitized = re.sub(r'_{2,}', '_', sanitized)  # Replace multiple underscores with single
    sanitized = sanitized.strip('_')  # Remove leading/trailing underscores
    
    # Limit length and ensure it's not empty
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip('_')
    
    if not sanitized:
        sanitized = 'video'
    
    return sanitized


def extract_video_title(url: str) -> str:
    """
    Extract video title from URL using yt-dlp.
    Returns sanitized title suitable for filename.
    """
    try:
        logger.info(f"🎬 Worker: Extracting video title from: {url}")
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Handle playlist URLs - take first video
            if 'entries' in info and info['entries']:
                info = info['entries'][0]
            
            title = info.get('title', 'Unknown Video')
            sanitized_title = sanitize_filename(title)
            
            logger.info(f"🎬 Worker: Video title: '{title}'")
            logger.info(f"🎬 Worker: Sanitized filename: '{sanitized_title}'")
            
            return sanitized_title
            
    except Exception as e:
        logger.warning(f"🎬 Worker: Failed to extract video title: {e}")
        return 'video'


def process_clip(job_id: str, url: str, in_ts: float, out_ts: float, format_id: Optional[str] = None, redis_connection=None) -> None:
    """
    Process a video clipping job:
    1. Download source with yt-dlp
    2. Slice clip with FFmpeg (smart key-frame fallback)  
    3. Save to local storage
    4. Update Redis job hash with progress & final URL
    """
    # Set up Redis connection for progress updates
    global worker_redis
    worker_redis = redis_connection
    
    # Start timing 
    start_time = time.monotonic()
    # clip_jobs_inflight.inc()  # Disabled for worker
    
    temp_dir = None
    source_file = None
    output_file = None
    job_status = "error"  # Default to error, will be updated to "done" on success
    
    try:
        logger.info(f"🎬 Worker: Starting job {job_id}: {url} [{in_ts}s - {out_ts}s] format: {format_id}")
        logger.info(f"🎬 Worker: Received format_id type: {type(format_id)}, value: {repr(format_id)}")
        logger.info(f"🎬 Worker: Clip duration requested: {out_ts - in_ts:.2f} seconds")
        
        # Extract video title for filename
        video_title = extract_video_title(url)
        logger.info(f"🎬 Worker: Using video title for filename: '{video_title}'")
        
        # Check if format_id is actually provided
        if format_id is None:
            logger.warning("🎬 Worker: format_id is None - resolution picker not working!")
        elif format_id == "None":
            logger.warning("🎬 Worker: format_id is string 'None' - check serialization!")
        else:
            logger.info(f"🎬 Worker: Using user-selected format: {format_id}")
            
        # Log timing details
        logger.info(f"🎬 Worker: TIMING ANALYSIS:")
        logger.info(f"🎬 Worker: - Start timestamp: {in_ts}s")
        logger.info(f"🎬 Worker: - End timestamp: {out_ts}s") 
        logger.info(f"🎬 Worker: - Expected duration: {out_ts - in_ts:.3f}s")
        
        # Validate input timestamps
        if in_ts < 0:
            logger.warning(f"🎬 Worker: ⚠️  Negative start timestamp: {in_ts}s")
        if out_ts <= in_ts:
            logger.error(f"🎬 Worker: ❌ Invalid timestamps: end ({out_ts}s) <= start ({in_ts}s)")
            raise Exception(f"INVALID_TIMESTAMPS: end ({out_ts}s) must be greater than start ({in_ts}s)")
        if (out_ts - in_ts) < 0.1:
            logger.warning(f"🎬 Worker: ⚠️  Very short clip duration: {out_ts - in_ts:.3f}s")
        
        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix=f"clip_{job_id}_"))
        
        # Step 1: Download source with yt-dlp
        update_job_progress(job_id, 5, JobStatus.working.value, "Initializing download...")
        
        source_file = temp_dir / f"{job_id}.%(ext)s"
        
        # Enhanced format selector with robust fallback for better compatibility
        if format_id and format_id != "None":
            # Build a comprehensive fallback chain for user-selected format
            # FIXED: Removed [ext=mp4] restriction to support m3u8/HLS streams
            format_selector = f'{format_id}+bestaudio/{format_id}/best[height<=720]/best'
            logger.info(f"🎬 Worker: Using selected format: {format_id} with robust fallback")
            logger.info(f"🎬 Worker: Format selector: {format_selector}")
            logger.info(f"🎬 Worker: Fallback chain: {format_id} -> 720p any format -> best available")
        else:
            # FIXED: Removed [ext=mp4] restriction to support m3u8/HLS streams  
            format_selector = 'best[height<=720]/best'
            logger.warning(f"🎬 Worker: No format_id provided (got: {repr(format_id)}), using default format selection")
            logger.warning(f"🎬 Worker: Default selector: {format_selector}")
            logger.warning("🎬 Worker: This indicates the resolution picker may not be working properly!")
        
        # Multiple yt-dlp configurations to try in order
        # Always respect user-selected format in first 3 attempts, fallback gracefully
        config_attempts = [
            # Attempt 1: Default configuration with user-selected format (WORKING as of 2025-06-13)
            {
                'outtmpl': str(source_file),
                'format': format_selector,
                'quiet': True,
                'no_warnings': True,
                'writesubtitles': False,
                'writeautomaticsub': False,
                'extract_flat': False,
            },
            # Attempt 2: Updated Android client configuration (2024) - ALWAYS RESPECTS USER FORMAT
            {
                'outtmpl': str(source_file),
                'format': format_selector,  # Always use user-selected format
                'quiet': True,
                'no_warnings': True,
                'writesubtitles': False,
                'writeautomaticsub': False,
                'extract_flat': False,
                # 'extractor_args': {
                #     'youtube': {
                #         'player_client': ['android_creator'],
                #         'skip': ['dash']
                #     }
                # },
                'http_headers': {
                    'User-Agent': 'com.google.android.apps.youtube.creator/24.47.100 (Linux; U; Android 14; SM-S918B) gzip',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
            },
            # Attempt 3: Web client with modern headers - ALWAYS RESPECTS USER FORMAT
            {
                'outtmpl': str(source_file),
                'format': format_selector,  # Always use user-selected format
                'quiet': True,
                'no_warnings': True,
                'writesubtitles': False,
                'writeautomaticsub': False,
                'extract_flat': False,
                # 'extractor_args': {
                #     'youtube': {
                #         'player_client': ['web'],
                #         'skip': ['dash', 'hls']
                #     }
                # },
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"'
                }
            },
            # Attempt 4: iOS client - PREFER USER FORMAT, FALLBACK IF NEEDED
            {
                'outtmpl': str(source_file),
                'format': format_selector if format_id else 'best[height<=720]/best',
                'quiet': True,
                'no_warnings': True,
                'writesubtitles': False,
                'writeautomaticsub': False,
                'extract_flat': False,
                # 'extractor_args': {
                #     'youtube': {
                #         'player_client': ['ios']
                #     }
                # },
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
            },
            # Attempt 5: Age-gate bypass attempt with embedded player - RESPECT USER FORMAT
            {
                'outtmpl': str(source_file),
                'format': format_selector if format_id else 'worst[ext=mp4]/worst',  # Respect user format, worst only if no preference
                'quiet': True,
                'no_warnings': True,
                'writesubtitles': False,
                'writeautomaticsub': False,
                'extract_flat': False,
                # 'extractor_args': {
                #     'youtube': {
                #         'player_client': ['web_embedded'],
                #         'skip': ['dash', 'hls']
                #     }
                # },
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://www.youtube.com/',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive'
                }
            }
        ]
        
        # Pre-validate format availability if user selected a specific format
        if format_id and format_id != "None":
            logger.info(f"🎬 Worker: Validating format {format_id} availability...")
            try:
                # Quick format validation without downloading
                validate_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                }
                with yt_dlp.YoutubeDL(validate_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if 'entries' in info and info['entries']:
                        info = info['entries'][0]
                    
                    available_formats = [f.get('format_id') for f in info.get('formats', [])]
                    logger.info(f"🎬 Worker: Available formats: {available_formats[:10]}...")  # Show first 10
                    
                    if format_id in available_formats:
                        logger.info(f"✅ Worker: Format {format_id} is available")
                    else:
                        logger.warning(f"⚠️ Worker: Format {format_id} NOT available! Backend provided incorrect format.")
                        logger.warning(f"🎬 Worker: This indicates backend metadata is stale or incorrect")
                        logger.warning(f"🎬 Worker: Will fall back to best available format")
                        # Override format selector to use fallback (FIXED: removed mp4 restriction)
                        format_selector = 'best[height<=720]/best'
                        logger.info(f"🎬 Worker: Updated format selector: {format_selector}")
                        
            except Exception as e:
                logger.warning(f"⚠️ Worker: Format validation failed: {e}")
                logger.warning(f"🎬 Worker: Proceeding with original format selector")
        
        # Try each configuration
        download_success = False
        last_error = None
        actual_format_used = None
        
        for i, ydl_opts in enumerate(config_attempts):
            try:
                logger.info(f"🎬 Worker: Attempt {i+1}: Trying download with config {i+1}")
                logger.info(f"🎬 Worker: Config {i+1} format selector: {ydl_opts.get('format', 'default')}")
                
                # Update progress for each attempt
                progress_base = 8 + (i * 3)  # Progress from 8 to 20 across attempts
                update_job_progress(job_id, progress_base, stage=f"Download attempt {i+1}/5...")
                
                # Update format selector in case it was changed during validation
                ydl_opts['format'] = format_selector
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    update_job_progress(job_id, progress_base + 1, stage=f"Extracting video info (attempt {i+1})...")
                    info = ydl.extract_info(url, download=True)
                    # Handle playlist URLs
                    if 'entries' in info and info['entries']:
                        info = info['entries'][0]
                    
                    # Log the actual format that was downloaded
                    actual_format_used = info.get('format_id', 'unknown')
                    actual_resolution = f"{info.get('width', 'unknown')}x{info.get('height', 'unknown')}"
                    requested_format = format_id if format_id and format_id != "None" else "auto"
                    
                    logger.info(f"🎬 Worker: Downloaded format: {actual_format_used}, resolution: {actual_resolution}")
                    logger.info(f"🎬 Worker: Requested: {requested_format}, Got: {actual_format_used}")
                    
                    if format_id and format_id != "None" and actual_format_used != format_id:
                        logger.warning(f"⚠️ Worker: Format mismatch! Requested {format_id}, got {actual_format_used}")
                        logger.warning(f"🎬 Worker: This confirms backend provided incorrect format data")
                    
                download_success = True
                logger.info(f"✅ Worker: Download successful with config {i+1}")
                break
            except Exception as e:
                last_error = e
                logger.warning(f"❌ Config {i+1} failed: {str(e)}")
                # Special handling for format not available errors
                if "Requested format is not available" in str(e):
                    logger.warning(f"🎬 Worker: Format {format_id} confirmed unavailable - backend metadata was wrong")
                # Clean up any partial files
                for f in temp_dir.glob(f"{job_id}.*"):
                    try:
                        f.unlink()
                    except:
                        pass
                continue
        
        if not download_success:
            raise Exception(f"YTDLP_FAIL: All download attempts failed. Last error: {str(last_error)}")
        
        # Find the actual downloaded file
        downloaded_files = list(temp_dir.glob(f"{job_id}.*"))
        if not downloaded_files:
            raise Exception("YTDLP_FAIL: No file downloaded")
        
        source_file = downloaded_files[0]
        logger.info(f"🎬 Worker: Downloaded: {source_file}")
        logger.info(f"🎬 Worker: File extension: {source_file.suffix}")
        logger.info(f"🎬 Worker: File size: {source_file.stat().st_size} bytes")
        
        # Validate that we got a video file, not HTML
        if source_file.suffix.lower() in ['.html', '.mhtml', '.htm']:
            raise Exception("YTDLP_FAIL: Downloaded HTML page instead of video - URL may be unavailable")
        
        # Ensure file has video-like extension or is recognizable by FFmpeg
        valid_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.m4v']
        if source_file.suffix.lower() not in valid_extensions:
            logger.warning(f"⚠️ Unexpected file extension: {source_file.suffix}. Proceeding with FFmpeg validation.")
        
        # Check if file has reasonable size (not just a small HTML file)
        file_size = source_file.stat().st_size
        if file_size < 1024:  # Less than 1KB is suspicious for video
            raise Exception(f"YTDLP_FAIL: Downloaded file is too small ({file_size} bytes) - likely not a video")
        
        # Step 3: Analyze downloaded video and decide encoding strategy
        update_job_progress(job_id, 30, stage="Analyzing video...")
        
        # First, analyze the actual downloaded file structure
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json', 
                '-show_streams',
                '-show_format',
                str(source_file)  # Use actual downloaded file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            video_info = json.loads(result.stdout)
            
            # Log stream information
            video_streams = [s for s in video_info.get('streams', []) if s.get('codec_type') == 'video']
            audio_streams = [s for s in video_info.get('streams', []) if s.get('codec_type') == 'audio']
            
            logger.info(f"🎬 Worker: Source analysis:")
            logger.info(f"🎬 Worker: - Video streams: {len(video_streams)}")
            logger.info(f"🎬 Worker: - Audio streams: {len(audio_streams)}")
            
            if video_streams:
                vs = video_streams[0]
                logger.info(f"🎬 Worker: - Video codec: {vs.get('codec_name', 'unknown')}")
                logger.info(f"🎬 Worker: - Resolution: {vs.get('width', '?')}x{vs.get('height', '?')}")
                logger.info(f"🎬 Worker: - Frame rate: {vs.get('avg_frame_rate', 'unknown')}")
                logger.info(f"🎬 Worker: - Pixel format: {vs.get('pix_fmt', 'unknown')}")
                
                # Check if we actually have video content
                if vs.get('codec_name') == 'none' or vs.get('width', 0) == 0:
                    logger.warning("🎬 Worker: ⚠️  Video stream appears to be empty or invalid!")
            else:
                logger.error("🎬 Worker: ❌ No video streams found in downloaded file!")
                raise Exception("VIDEO_FAIL: Downloaded file contains no video streams")
                
            if audio_streams:
                aud = audio_streams[0]
                logger.info(f"🎬 Worker: - Audio codec: {aud.get('codec_name', 'unknown')}")
                logger.info(f"🎬 Worker: - Sample rate: {aud.get('sample_rate', 'unknown')}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"🎬 Worker: Failed to analyze source video: {e}")
            raise Exception(f"VIDEO_FAIL: Cannot analyze downloaded video file: {e}")
        except Exception as e:
            logger.warning(f"🎬 Worker: Video analysis warning: {e}")
        
        update_job_progress(job_id, 25, stage="Analyzing video...")
        
        # Additional progress updates during analysis
        logger.info("🎬 Worker: Video download completed successfully")
        
        update_job_progress(job_id, 30, stage="Preparing video processing...")
        
        # Detect if rotation correction is needed (use actual source file)
        rotation_filter = detect_video_rotation(source_file)
        
        # CRITICAL FIX: Apply systematic tilt correction for all videos
        # User reports ALL videos have same clockwise tilt regardless of source
        # This indicates a processing pipeline issue that needs universal correction
        if not rotation_filter:
            # FIXED: Use rotation with scale to ensure even dimensions for H.264 compatibility
            # H.264 requires even width/height, rotation can create odd dimensions (e.g., 646x371)
            # Scale to next even dimensions after rotation to prevent encoding errors
            rotation_filter = 'rotate=-1*PI/180:fillcolor=black,scale=trunc(iw/2)*2:trunc(ih/2)*2'
            logger.info("🎬 Worker: Applying systematic tilt correction (-1° counter-clockwise with even dimension scaling)")
        
        if rotation_filter:
            logger.info(f"🎬 Worker: Applying rotation correction: {rotation_filter}")
        else:
            logger.info("🎬 Worker: No rotation correction needed")
        
        # Find keyframes using the actual source file
        logger.info(f"🎬 Worker: KEYFRAME ANALYSIS:")
        keyframe_ts = find_nearest_keyframe(str(source_file), in_ts)
        needs_reencode = abs(keyframe_ts - in_ts) > 1.0  # Re-encode if >1s from keyframe
        
        logger.info(f"🎬 Worker: - Requested start: {in_ts}s")
        logger.info(f"🎬 Worker: - Nearest keyframe: {keyframe_ts}s")
        logger.info(f"🎬 Worker: - Keyframe offset: {abs(keyframe_ts - in_ts):.3f}s")
        logger.info(f"🎬 Worker: - Needs re-encode: {needs_reencode}")
        
        # Log which FFmpeg strategy will be used
        if needs_reencode:
            logger.info(f"🎬 Worker: STRATEGY: Two-pass processing (re-encode + copy)")
        else:
            logger.info(f"🎬 Worker: STRATEGY: Single-pass stream copy")
        
        # Step 4: Clip video with FFmpeg
        update_job_progress(job_id, 35, stage="Starting video processing...")
        
        # More granular progress updates
        logger.info("🎬 Worker: Beginning FFmpeg processing stage")
        
        output_file = temp_dir / f"{job_id}_output.mp4"
        
        if needs_reencode:
            # Re-encode first GOP, then copy rest
            first_gop_duration = min(2.0, out_ts - in_ts)  # Max 2 seconds for first GOP
            gop_end = in_ts + first_gop_duration
            
            # First pass: re-encode the first GOP
            temp_gop_file = temp_dir / f"{job_id}_gop.mp4"
            cmd_gop = [
                settings.ffmpeg_path.replace('/usr/local/bin/ffmpeg', '/usr/bin/ffmpeg'),
                '-i', str(source_file),
                '-ss', str(in_ts),
                '-to', str(gop_end),
            ]
            
            # Add rotation filter if needed, otherwise use copy
            if rotation_filter:
                cmd_gop.extend(['-vf', rotation_filter])
                cmd_gop.extend([
                    '-c:v', 'libx264',
                    '-preset', 'veryfast',
                    '-crf', '18',
                    '-c:a', 'aac',  # Ensure audio compatibility
                    '-b:a', '128k',
                ])
            else:
                # CRITICAL FIX: Use re-encoding for accurate timestamps (same as single-pass fix)
                cmd_gop.extend([
                    '-c:v', 'libx264',  # Re-encode video for accurate timestamps
                    '-preset', 'veryfast',  # Fast encoding preset
                    '-crf', '18',  # High quality constant rate factor
                    '-c:a', 'aac',  # Re-encode audio for compatibility
                    '-b:a', '128k',  # Audio bitrate
                ])
                
            cmd_gop.extend([
                '-avoid_negative_ts', 'make_zero',
                str(temp_gop_file),
                '-y'
            ])
            
            update_job_progress(job_id, 45, stage="Processing first segment...")
            result = subprocess.run(cmd_gop, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"🎬 Worker: GOP FFmpeg command failed: {' '.join(cmd_gop)}")
                logger.error(f"🎬 Worker: GOP FFmpeg stderr: {result.stderr}")
                raise Exception(f"FFMPEG_FAIL: GOP re-encode failed: {result.stderr}")
            
            update_job_progress(job_id, 55, stage="Processing remaining segments...")
            
            # Second pass: copy the rest if needed
            if gop_end < out_ts:
                temp_rest_file = temp_dir / f"{job_id}_rest.mp4"
                cmd_rest = [
                    settings.ffmpeg_path.replace('/usr/local/bin/ffmpeg', '/usr/bin/ffmpeg'),
                    '-i', str(source_file),
                    '-ss', str(gop_end),
                    '-to', str(out_ts),
                ]
                
                # Add rotation filter if needed, otherwise use copy
                if rotation_filter:
                    cmd_rest.extend(['-vf', rotation_filter])
                    cmd_rest.extend([
                        '-c:v', 'libx264',
                        '-preset', 'veryfast', 
                        '-crf', '18',
                        '-c:a', 'aac',  # Ensure audio compatibility
                        '-b:a', '128k',
                    ])
                else:
                    # CRITICAL FIX: Use re-encoding for accurate timestamps (same as single-pass fix)
                    cmd_rest.extend([
                        '-c:v', 'libx264',  # Re-encode video for accurate timestamps
                        '-preset', 'veryfast',  # Fast encoding preset
                        '-crf', '18',  # High quality constant rate factor
                        '-c:a', 'aac',  # Re-encode audio for compatibility
                        '-b:a', '128k',  # Audio bitrate
                    ])
                    
                cmd_rest.extend([
                    '-avoid_negative_ts', 'make_zero',
                    str(temp_rest_file),
                    '-y'
                ])
                
                update_job_progress(job_id, 65, stage="Processing final segment...")
                result = subprocess.run(cmd_rest, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error(f"🎬 Worker: Rest FFmpeg command failed: {' '.join(cmd_rest)}")
                    logger.error(f"🎬 Worker: Rest FFmpeg stderr: {result.stderr}")
                    raise Exception(f"FFMPEG_FAIL: Rest copy failed: {result.stderr}")
                
                # Concatenate both parts
                concat_list = temp_dir / f"{job_id}_concat.txt"
                concat_list.write_text(f"file '{temp_gop_file}'\nfile '{temp_rest_file}'\n")
                
                cmd_concat = [
                    settings.ffmpeg_path.replace('/usr/local/bin/ffmpeg', '/usr/bin/ffmpeg'),
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', str(concat_list),
                    '-c', 'copy',
                    str(output_file),
                    '-y'
                ]
                
                update_job_progress(job_id, 75, stage="Combining video segments...")
                result = subprocess.run(cmd_concat, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error(f"🎬 Worker: Concat FFmpeg command failed: {' '.join(cmd_concat)}")
                    logger.error(f"🎬 Worker: Concat FFmpeg stderr: {result.stderr}")
                    raise Exception(f"FFMPEG_FAIL: Concatenation failed: {result.stderr}")
            else:
                # Only first GOP needed
                output_file = temp_gop_file
        else:
            # Simple processing - use stream copy when no rotation needed
            logger.info(f"🎬 Worker: SINGLE-PASS PROCESSING:")
            logger.info(f"🎬 Worker: - Input file: {source_file}")
            logger.info(f"🎬 Worker: - Start time: {in_ts}s")
            logger.info(f"🎬 Worker: - End time: {out_ts}s")
            logger.info(f"🎬 Worker: - Duration: {out_ts - in_ts:.3f}s")
            
            # Use precise timestamp formatting for FFmpeg
            # FFmpeg can be sensitive to timestamp precision
            start_time_str = f"{in_ts:.6f}"  # 6 decimal places for microsecond precision
            end_time_str = f"{out_ts:.6f}"
            duration_str = f"{out_ts - in_ts:.6f}"
            
            logger.info(f"🎬 Worker: PRECISE TIMESTAMPS:")
            logger.info(f"🎬 Worker: - Start: {start_time_str}s")
            logger.info(f"🎬 Worker: - End: {end_time_str}s")
            logger.info(f"🎬 Worker: - Duration: {duration_str}s")
            
            # Use -ss (seek start) and -t (duration) instead of -to (end time)
            # This is more reliable for accurate duration clipping
            cmd_process = [
                settings.ffmpeg_path.replace('/usr/local/bin/ffmpeg', '/usr/bin/ffmpeg'),
                '-i', str(source_file),
                '-ss', start_time_str,
                '-t', duration_str,  # Use duration instead of end time for better accuracy
            ]
            
            logger.info(f"🎬 Worker: Using -ss (start) + -t (duration) method for accuracy")
            
            if rotation_filter:
                # Need to re-encode for rotation correction
                cmd_process.extend(['-vf', rotation_filter])
                cmd_process.extend([
                    '-c:v', 'libx264',
                    '-preset', 'veryfast',
                    '-crf', '18',
                    '-c:a', 'aac',  # Ensure audio compatibility
                    '-b:a', '128k',
                ])
                logger.info("🎬 Worker: ENCODING MODE: Re-encoding for rotation correction")
            else:
                # CRITICAL FIX: Use re-encoding instead of stream copy for accurate timestamps
                # Stream copy (-c copy) cannot handle non-keyframe start times accurately
                # See: https://ericswpark.com/blog/2022/2022-12-03-ffmpeg-cut-videos-to-the-exact-frame/
                cmd_process.extend([
                    '-c:v', 'libx264',  # Re-encode video for accurate timestamps
                    '-preset', 'veryfast',  # Fast encoding preset
                    '-crf', '18',  # High quality constant rate factor
                    '-c:a', 'aac',  # Re-encode audio for compatibility
                    '-b:a', '128k',  # Audio bitrate
                ])
                logger.info("🎬 Worker: ENCODING MODE: Re-encoding for accurate timestamp cutting")
                
            cmd_process.extend([
                '-avoid_negative_ts', 'make_zero',
                str(output_file),
                '-y'
            ])
            
            logger.info(f"🎬 Worker: FFMPEG COMMAND:")
            logger.info(f"🎬 Worker: {' '.join(cmd_process)}")
            logger.info(f"🎬 Worker: Expected output: {output_file}")
            
            # Run FFmpeg and capture timing
            logger.info(f"🎬 Worker: Starting FFmpeg processing...")
            logger.info(f"🎬 Worker: Command: {' '.join(cmd_process)}")
            update_job_progress(job_id, 40, stage="Processing video with FFmpeg...")
            ffmpeg_start = time.time()
            
            # Execute FFmpeg with detailed logging
            result = subprocess.run(cmd_process, capture_output=True, text=True)
            ffmpeg_duration = time.time() - ffmpeg_start
            
            logger.info(f"🎬 Worker: FFmpeg completed in {ffmpeg_duration:.2f}s")
            
            if result.returncode != 0:
                logger.error(f"🎬 Worker: ❌ FFmpeg failed with return code: {result.returncode}")
                logger.error(f"🎬 Worker: ❌ FFmpeg command: {' '.join(cmd_process)}")
                logger.error(f"🎬 Worker: ❌ FFmpeg stderr: {result.stderr}")
                logger.error(f"🎬 Worker: ❌ FFmpeg stdout: {result.stdout}")
                # Enhanced error reporting
                if "height not divisible by 2" in result.stderr:
                    logger.error("🎬 Worker: ❌ DIMENSION ERROR: Video dimensions are not even (H.264 requirement)")
                elif "No such file or directory" in result.stderr:
                    logger.error("🎬 Worker: ❌ FILE ERROR: Input file not found or corrupted")
                elif "Invalid data" in result.stderr:
                    logger.error("🎬 Worker: ❌ DATA ERROR: Corrupted video stream")
                update_job_error(job_id, "FFMPEG_FAIL", f"Video processing failed: {result.stderr[:200]}")
                raise Exception(f"FFMPEG_FAIL: Processing failed: {result.stderr}")
            else:
                logger.info("🎬 Worker: ✅ FFmpeg processing completed successfully")
                update_job_progress(job_id, 70, stage="Video processing complete")
                if result.stderr:  # FFmpeg often outputs info to stderr even on success
                    logger.info(f"🎬 Worker: FFmpeg info: {result.stderr[-500:]}")  # Last 500 chars
        
        update_job_progress(job_id, 80, stage="Validating output...")
        
        logger.info(f"🎬 Worker: OUTPUT FILE VALIDATION:")
        
        if not output_file.exists():
            logger.error(f"🎬 Worker: ❌ Output file does not exist: {output_file}")
            raise Exception("FFMPEG_FAIL: Output file was not created")
        
        output_size = output_file.stat().st_size
        logger.info(f"🎬 Worker: - File exists: ✅")
        logger.info(f"🎬 Worker: - File size: {output_size:,} bytes ({output_size/1024/1024:.2f} MB)")
        
        if output_size == 0:
            logger.error(f"🎬 Worker: ❌ Output file is empty!")
            raise Exception("FFMPEG_FAIL: Output file is empty")
        
        # Check for reasonable file size (at least 1KB for video)
        if output_size < 1024:
            logger.warning(f"🎬 Worker: ⚠️  Output file is very small: {output_size} bytes")
            
        logger.info(f"🎬 Worker: Clipped video created successfully")
        
        # Validate the output file has video content
        try:
            cmd_validate = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                str(output_file)
            ]
            
            result = subprocess.run(cmd_validate, capture_output=True, text=True, check=True)
            output_info = json.loads(result.stdout)
            
            output_video_streams = [s for s in output_info.get('streams', []) if s.get('codec_type') == 'video']
            output_audio_streams = [s for s in output_info.get('streams', []) if s.get('codec_type') == 'audio']
            
            logger.info(f"🎬 Worker: Output validation:")
            logger.info(f"🎬 Worker: - Video streams: {len(output_video_streams)}")
            logger.info(f"🎬 Worker: - Audio streams: {len(output_audio_streams)}")
            
            if not output_video_streams:
                logger.error("🎬 Worker: ❌ Output file has no video streams!")
                raise Exception("VIDEO_FAIL: Output file contains no video content")
            
            if output_video_streams:
                vs = output_video_streams[0]
                actual_duration = float(vs.get('duration', 0))
                expected_duration = out_ts - in_ts
                
                logger.info(f"🎬 Worker: - Output resolution: {vs.get('width', '?')}x{vs.get('height', '?')}")
                logger.info(f"🎬 Worker: - Output codec: {vs.get('codec_name', 'unknown')}")
                logger.info(f"🎬 Worker: - Output duration: {actual_duration:.3f}s")
                logger.info(f"🎬 Worker: - Expected duration: {expected_duration:.3f}s")
                
                # CRITICAL: Check for duration mismatch
                duration_diff = abs(actual_duration - expected_duration)
                if duration_diff > 0.5:  # More than 0.5 second difference
                    logger.error(f"🎬 Worker: ❌ DURATION MISMATCH!")
                    logger.error(f"🎬 Worker: - Expected: {expected_duration:.3f}s")
                    logger.error(f"🎬 Worker: - Actual: {actual_duration:.3f}s")
                    logger.error(f"🎬 Worker: - Difference: {duration_diff:.3f}s")
                    logger.error(f"🎬 Worker: This explains the user's complaint about short video!")
                else:
                    logger.info(f"🎬 Worker: ✅ Duration matches expected ({duration_diff:.3f}s difference)")
                
        except Exception as e:
            logger.warning(f"🎬 Worker: Could not validate output file: {e}")
            # Don't fail the job for validation issues, just warn
        
        # Step 5: Save to storage using new storage manager
        update_job_progress(job_id, 85, stage="Preparing upload...")
        logger.info("🎬 Worker: ✅ Output validation complete, preparing storage upload")
        
        try:
            # Read processed video data synchronously for now (async will be handled by manager)
            update_job_progress(job_id, 87, stage="Reading processed video...")
            with open(output_file, 'rb') as f:
                video_data = f.read()
            
            logger.info(f"🎬 Worker: Read {len(video_data):,} bytes for upload")
            
            # Get storage manager and save file
            update_job_progress(job_id, 90, stage="Uploading to storage...")
            storage_manager = get_storage_manager()
            
            # Run async save operation in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                storage_result = loop.run_until_complete(
                    storage_manager.save(job_id, video_data, video_title)
                )
            finally:
                loop.close()
            
            update_job_progress(job_id, 95, stage="Generating download link...")
            # Generate download URL using new API
            download_url = storage_manager.get_download_url(job_id, storage_result["filename"])
            
            logger.info(f"🎬 Worker: File saved to storage:")
            logger.info(f"🎬 Worker: - Path: {storage_result['file_path']}")
            logger.info(f"🎬 Worker: - Size: {storage_result['size']:,} bytes")
            logger.info(f"🎬 Worker: - SHA256: {storage_result['sha256'][:16]}...")
            logger.info(f"🎬 Worker: - Download URL: {download_url}")
            
        except Exception as e:
            raise Exception(f"STORAGE_FAIL: Failed to save clip: {str(e)}")
        
        # Step 6: Mark as done with enhanced metadata
        update_job_progress(job_id, 98, stage="Finalizing...")
        job_key = f"job:{job_id}"
        completion_data = {
            "status": str(JobStatus.done.value),
            "progress": "100",
            "download_url": str(download_url),
            "video_title": str(video_title),
            "file_size": str(storage_result["size"]),
            "file_sha256": str(storage_result["sha256"]),
            "completed_at": str(datetime.utcnow().isoformat())
        }
        redis_connection.hset(job_key, mapping=completion_data)
        redis_connection.expire(job_key, 3600)
        
        # Final progress update
        update_job_progress(job_id, 100, JobStatus.done.value, "Complete! Ready for download")
        logger.info(f"✅ Job {job_id} marked as completed with download URL")
        
        job_status = "done"  # Update status for metrics
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {str(e)}")
        
        # Extract error code from exception message
        error_message = str(e)
        if error_message.startswith(('YTDLP_FAIL:', 'FFMPEG_FAIL:', 'UPLOAD_FAIL:')):
            error_code, _, msg = error_message.partition(':')
            update_job_error(job_id, error_code.strip(), msg.strip())
        else:
            update_job_error(job_id, 'UNKNOWN_ERROR', error_message)
        
        raise  # Re-raise for RQ to handle
        
    finally:
        # Cleanup temporary files
        if temp_dir and temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                logger.error(f"Failed to cleanup temp dir {temp_dir}: {e}")
        
        # Calculate job latency and update metrics
        job_latency = time.monotonic() - start_time
        logger.info(f"Job {job_id} took {job_latency:.2f}s (status: {job_status})")
        # clip_job_latency_seconds.labels(status=job_status).observe(job_latency)  # Disabled for worker
        
        # Decrement inflight gauge  
        # clip_jobs_inflight.dec()  # Disabled for worker 