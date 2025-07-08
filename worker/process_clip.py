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
import traceback

import yt_dlp
import aiofiles

# Import from backend app
sys.path.append("/app/backend")
from app import settings
from app.models import JobStatus
from app.storage_factory import get_storage_manager

# Import video processing components
from worker.video.trimmer import VideoTrimmer
from worker.progress.tracker import ProgressTracker

# Import Instagram-specific yt-dlp configuration
from worker.utils.ytdlp_options import (
    build_common_ydl_opts,
    build_instagram_ydl_configs,
    is_instagram_url,
)

# Redis will be passed as parameter from main worker
worker_redis = None
# Simplified metrics - avoid Prometheus import issues in worker
# from app.metrics import clip_job_latency_seconds, clip_jobs_inflight

logger = logging.getLogger(__name__)


def update_job_progress(
    job_id: str,
    progress: int,
    status: Optional[str] = None,
    stage: Optional[str] = None,
):
    """Update job progress and status in Redis"""
    try:
        if not worker_redis:
            logger.warning(
                f"⚠️ Redis not available, cannot update job {job_id} progress"
            )
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
        logger.info(
            f"📊 Job {job_id} progress: {progress}% {f'({status})' if status else ''}{stage_msg}"
        )
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
            "progress": "0",  # Use "0" instead of null for error state
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
            settings.ffmpeg_path.replace("/usr/local/bin/ffmpeg", "/usr/bin/ffprobe"),
            "-v",
            "quiet",
            "-select_streams",
            "v:0",
            "-show_entries",
            "frame=pkt_pts_time,key_frame",
            "-of",
            "csv=print_section=0",
            video_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        keyframes = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split(",")
                if len(parts) >= 2 and parts[1] == "1":  # key_frame=1
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
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_streams",
            str(video_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        metadata = json.loads(result.stdout)

        for stream in metadata.get("streams", []):
            if stream.get("codec_type") == "video":
                width = stream.get("width", 0)
                height = stream.get("height", 0)

                # Check for rotation in side data (Display Matrix)
                side_data = stream.get("side_data_list", [])
                for data in side_data:
                    if data.get("side_data_type") == "Display Matrix":
                        rotation = data.get("rotation", 0)
                        if rotation:
                            logger.info(
                                f"Found rotation metadata in Display Matrix: {rotation}°"
                            )
                            # Convert rotation to appropriate transpose filter
                            if rotation == 90 or rotation == -270:
                                return "transpose=2"  # 90° counterclockwise
                            elif rotation == -90 or rotation == 270:
                                return "transpose=1"  # 90° clockwise
                            elif rotation == 180 or rotation == -180:
                                return "transpose=1,transpose=1"  # 180°

                # Check for rotation in stream tags
                tags = stream.get("tags", {})
                if "rotate" in tags:
                    rotation = int(tags["rotate"])
                    logger.info(f"Found rotation tag: {rotation}°")
                    if rotation == 90:
                        return "transpose=2"  # 90° counterclockwise
                    elif rotation == -90 or rotation == 270:
                        return "transpose=1"  # 90° clockwise
                    elif rotation == 180:
                        return "transpose=1,transpose=1"  # 180°

                # ENHANCED: Check for visual rotation based on aspect ratio and encoding patterns
                # If video is portrait (height > width) but appears rotated from mobile source
                if height > width and width > 0 and height > 0:
                    aspect_ratio = height / width

                    # Check if this looks like a rotated landscape video
                    # Common mobile video resolutions when rotated incorrectly:
                    # 360x640 (should be 640x360), 480x854 (should be 854x480), etc.
                    if (
                        aspect_ratio > 1.5
                    ):  # Very tall aspect ratio suggests rotation issue
                        # Check encoding signature for mobile/YouTube sources that often have rotation issues
                        encoder = tags.get("encoder", "").lower()
                        handler = tags.get("handler_name", "").lower()

                        # YouTube and mobile encoders often have slight visual tilt issues
                if "google" in handler or "youtube" in handler:
                    logger.info(
                        f"Detected Google/YouTube video with potential tilt: {width}x{height} from {handler}"
                    )
                    # Apply small counter-clockwise rotation to fix typical clockwise camera tilt
                    # This addresses the visual tilt issue reported by users
                    logger.info(
                        "Applying 1° counter-clockwise tilt correction for YouTube video"
                    )
                    return (
                        "rotate=-1*PI/180:fillcolor=black"  # -1° to fix clockwise tilt
                    )
                elif "android" in handler or "lavc" in encoder or "x264" in encoder:
                    # For other mobile sources, only apply transpose for true portrait videos
                    if height > width and aspect_ratio > 1.5:
                        logger.info(
                            f"Detected mobile portrait content: {width}x{height} from {handler}"
                        )
                        logger.info(
                            "Applying 90° counter-clockwise correction for mobile portrait"
                        )
                        return "transpose=2"  # 90° counter-clockwise for true portrait

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
    if not title or title.strip() == "":
        return "video"

    # Remove or replace problematic characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", title)  # Replace invalid filename chars
    sanitized = re.sub(r"[^\w\s\-_\.\(\)\[\]]", "", sanitized)  # Keep only safe chars
    sanitized = re.sub(r"\s+", "_", sanitized)  # Replace spaces with underscores
    sanitized = re.sub(
        r"_{2,}", "_", sanitized
    )  # Replace multiple underscores with single
    sanitized = sanitized.strip("_")  # Remove leading/trailing underscores

    # Limit length and ensure it's not empty
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip("_")

    if not sanitized:
        sanitized = "video"

    return sanitized


def extract_video_title(url: str) -> str:
    """
    Extract video title from URL using yt-dlp.
    Returns sanitized title suitable for filename.
    """
    try:
        logger.info(f"🎬 Worker: Extracting video title from: {url}")

        # Use Instagram-specific configuration for title extraction if needed
        if is_instagram_url(url):
            instagram_configs = build_instagram_ydl_configs()

            # Try each config for title extraction
            for config_idx, base_config in enumerate(instagram_configs, 1):
                try:
                    ydl_opts = {**base_config}
                    ydl_opts["extract_flat"] = False
                    ydl_opts["skip_download"] = True

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)

                        # Handle playlist URLs - take first video
                        if "entries" in info and info["entries"]:
                            info = info["entries"][0]

                        title = info.get("title", "Unknown Video")
                        sanitized_title = sanitize_filename(title)

                        logger.info(
                            f"🎬 Worker: Video title: '{title}' (using config {config_idx})"
                        )
                        logger.info(
                            f"🎬 Worker: Sanitized filename: '{sanitized_title}'"
                        )

                        return sanitized_title

                except Exception as e:
                    logger.warning(
                        f"🎬 Worker: Title extraction config {config_idx} failed: {e}"
                    )
                    if config_idx == len(instagram_configs):
                        # If all configs failed, return default
                        logger.warning(
                            "🎬 Worker: All Instagram title extraction methods failed, using default"
                        )
                        return "instagram_video"
                    continue
        else:
            ydl_opts = build_common_ydl_opts()
            ydl_opts["extract_flat"] = False

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                # Handle playlist URLs - take first video
                if "entries" in info and info["entries"]:
                    info = info["entries"][0]

                title = info.get("title", "Unknown Video")
                sanitized_title = sanitize_filename(title)

                logger.info(f"🎬 Worker: Video title: '{title}'")
                logger.info(f"🎬 Worker: Sanitized filename: '{sanitized_title}'")

                return sanitized_title

    except Exception as e:
        logger.warning(f"🎬 Worker: Failed to extract video title: {e}")
        return "video"


def process_clip(
    job_id: str,
    url: str,
    in_ts: float,
    out_ts: float,
    resolution: Optional[str] = None,
    redis_connection=None,
) -> None:
    """
    Main function to process a video clip.
    Orchestrates downloading, trimming, and storing the video.
    """
    global worker_redis
    worker_redis = redis_connection

    job_start_time = time.time()

    # Log initial job parameters
    logger.info(
        f"🎬 Worker: Starting job {job_id}: {url} [{in_ts:.2f}s - {out_ts:.2f}s] resolution: {resolution}"
    )

    clip_duration = out_ts - in_ts
    if clip_duration <= 0:
        update_job_error(
            job_id, "INVALID_TIMESTAMPS", "End time must be after start time."
        )
        return

    logger.info(f"🎬 Worker: Clip duration requested: {clip_duration:.2f} seconds")

    # Create a temporary directory for processing
    with tempfile.TemporaryDirectory(prefix=f"clip_{job_id}_") as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        try:
            # Step 1: Download Video
            # ---------------------
            update_job_progress(
                job_id,
                5,
                status=JobStatus.working.value,
                stage="Initializing download...",
            )

            # --- Robust Format Selection based on Resolution ---
            if resolution and "x" in resolution:
                try:
                    height = int(resolution.split("x")[1])
                    # Prefer mp4, fallback to best available
                    format_selector = f"best[height<={height}][ext=mp4]/best[height<={height}]/best[ext=mp4]/best"
                except (IndexError, ValueError):
                    logger.warning(
                        f"⚠️ Invalid resolution format '{resolution}'. Falling back to default 'best'."
                    )
                    format_selector = "best[ext=mp4]/best"
            else:
                logger.info("No resolution provided, using default 'best' format.")
                format_selector = "best[ext=mp4]/best"

            logger.info(f"🎬 Worker: Using format selector: '{format_selector}'")

            temp_video_path = temp_dir / f"{job_id}_source.%(ext)s"

            # Use Instagram-specific configuration with fallback strategies
            if is_instagram_url(url):
                logger.info(
                    "🎬 Worker: Using Instagram-specific configuration with multiple fallback strategies"
                )
                instagram_configs = build_instagram_ydl_configs()
                download_successful = False
                downloaded_file = None
                last_error = None

                for config_idx, base_config in enumerate(instagram_configs, 1):
                    try:
                        logger.info(
                            f"🎬 Worker: Trying Instagram config {config_idx}/{len(instagram_configs)}"
                        )

                        # Log configuration details for debugging
                        has_cookies = base_config.get("cookiefile") is not None
                        has_browser = base_config.get("cookiesfrombrowser") is not None
                        user_agent = base_config.get("http_headers", {}).get(
                            "User-Agent", "None"
                        )[:50]
                        logger.info(
                            f"🔧 Config {config_idx}: cookies={has_cookies}, browser={has_browser}, UA={user_agent}..."
                        )

                        ydl_opts = {
                            **base_config,
                            "format": format_selector,
                            "outtmpl": str(temp_video_path),
                            "fragment_retries": 3,
                            "http_chunk_size": 20971520,  # 20MB in bytes
                            "noprogress": True,
                        }

                        def progress_hook(d):
                            """Robust progress hook that handles missing 'progress' key"""
                            try:
                                if "downloaded_bytes" in d and "total_bytes" in d:
                                    progress = d["downloaded_bytes"] / d["total_bytes"]
                                    update_job_progress(
                                        job_id,
                                        int(progress * 0.25) + 5,
                                        stage="Downloading",
                                    )
                                elif "progress" in d:
                                    update_job_progress(
                                        job_id,
                                        int(d["progress"] * 0.25) + 5,
                                        stage="Downloading",
                                    )
                                elif d.get("status") == "downloading":
                                    update_job_progress(job_id, 10, stage="Downloading")
                            except (KeyError, TypeError, ZeroDivisionError):
                                pass

                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            ydl.add_progress_hook(progress_hook)
                            info = ydl.extract_info(url, download=True)
                            downloaded_file = ydl.prepare_filename(info)
                            download_successful = True
                            logger.info(
                                f"🎬 Worker: Instagram download successful with config {config_idx}"
                            )
                            break

                    except Exception as e:
                        error_msg = str(e).lower()
                        last_error = e
                        logger.warning(
                            f"🎬 Worker: Instagram config {config_idx} failed: {e}"
                        )

                        # Continue to next config for any error, log details for last attempt
                        if config_idx < len(instagram_configs):
                            continue

                        # If this is the last config, provide comprehensive error message
                        if (
                            "rate-limit" in error_msg
                            or "login required" in error_msg
                            or "authentication" in error_msg
                        ):
                            auth_help_msg = (
                                "Instagram requires authentication for this content. To fix this:\n\n"
                                "1. Add Instagram cookies: Create 'cookies/instagram_cookies.txt' with valid session cookies\n"
                                "2. Use browser extraction: Ensure Chrome/Firefox is available for automatic cookie extraction\n"
                                "3. Try a different Instagram URL: Some content requires login while others don't\n"
                                "4. Contact support if this is a public Instagram post\n\n"
                                f"Tried {len(instagram_configs)} different configurations. "
                                "See logs for detailed debugging information."
                            )
                            raise Exception(auth_help_msg)
                        else:
                            technical_msg = (
                                f"Instagram download failed after trying {len(instagram_configs)} configurations. "
                                f"Last error: {str(last_error)[:200]}... "
                                "This may be due to Instagram API changes or network issues. "
                                "Please try again later or contact support."
                            )
                            raise Exception(technical_msg)

                if not download_successful:
                    raise Exception(
                        f"All {len(instagram_configs)} Instagram download strategies failed. Last error: {last_error}"
                    )

            else:
                # Use standard configuration for other platforms
                base_opts = build_common_ydl_opts()
                ydl_opts = {
                    **base_opts,
                    "format": format_selector,
                    "outtmpl": str(temp_video_path),
                    "retries": 3,
                    "fragment_retries": 3,
                    "http_chunk_size": 20971520,  # 20MB in bytes
                    "noprogress": True,
                }

                download_start_time = time.time()
                logger.info("🎬 Worker: Starting video download with yt-dlp...")

                downloaded_file = None

                def progress_hook(d):
                    """Robust progress hook that handles missing 'progress' key"""
                    try:
                        if "downloaded_bytes" in d and "total_bytes" in d:
                            progress = d["downloaded_bytes"] / d["total_bytes"]
                            update_job_progress(
                                job_id, int(progress * 0.25) + 5, stage="Downloading"
                            )
                        elif "progress" in d:
                            update_job_progress(
                                job_id,
                                int(d["progress"] * 0.25) + 5,
                                stage="Downloading",
                            )
                        # If no progress info available, just update stage without progress
                        elif d.get("status") == "downloading":
                            update_job_progress(job_id, 10, stage="Downloading")
                    except (KeyError, TypeError, ZeroDivisionError) as e:
                        # Silently continue if progress calculation fails
                        pass

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.add_progress_hook(progress_hook)
                    info = ydl.extract_info(url, download=True)
                    downloaded_file = ydl.prepare_filename(info)

            if not downloaded_file or not os.path.exists(downloaded_file):
                raise Exception("yt-dlp failed to download the file.")

            logger.info(f"🎬 Worker: Downloaded to: {downloaded_file}")

            # 2. Trim the video
            update_job_progress(job_id, 30, stage="Trimming video...")

            # Create progress tracker for trimming
            progress_tracker = ProgressTracker(job_id, worker_redis)

            # Initialize video trimmer
            trimmer = VideoTrimmer(progress_tracker)

            # Trim the video
            logger.info(f"🎬 Worker: Starting video trim from {in_ts}s to {out_ts}s")
            trimmed_file = asyncio.run(
                trimmer.trim(Path(downloaded_file), in_ts, out_ts)
            )

            if not trimmed_file.exists():
                raise Exception("Video trimming failed - output file not created")

            logger.info(f"🎬 Worker: Video trimmed successfully: {trimmed_file}")

            # 3. Upload to storage
            update_job_progress(job_id, 80, stage="Uploading...")

            # Get video title for filename
            video_title = extract_video_title(url)
            final_filename = f"{video_title}_{job_id[:8]}.mp4"

            # Upload to storage
            storage_manager = get_storage_manager()
            try:
                with open(trimmed_file, "rb") as f:
                    file_content = f.read()

                # Use the correct method signature for LocalStorageManager.save()
                storage_result = asyncio.run(
                    storage_manager.save(
                        job_id=job_id, video_data=file_content, video_title=video_title
                    )
                )

                # Generate download URL using the storage manager's method
                download_url = storage_manager.get_download_url(
                    job_id, storage_result["filename"]
                )

                logger.info(f"🎬 Worker: File uploaded successfully: {download_url}")
                logger.info(f"🎬 Worker: File path: {storage_result['file_path']}")
                logger.info(f"🎬 Worker: File size: {storage_result['size']:,} bytes")

                # Update job with completion
                update_job_progress(
                    job_id, 100, status=JobStatus.done.value, stage="Complete"
                )

                # Update job with download URL
                job_key = f"job:{job_id}"
                worker_redis.hset(
                    job_key,
                    mapping={
                        "download_url": download_url,
                        "file_size": str(storage_result["size"]),
                        "video_title": video_title,
                    },
                )

                logger.info(f"🎬 Worker: Job {job_id} completed successfully")

            except Exception as upload_error:
                logger.error(f"❌ Upload failed for job {job_id}: {upload_error}")
                raise Exception(f"Upload failed: {upload_error}")

        except Exception as e:
            logger.error(f"❌ Job {job_id} failed during processing: {e}")
            logger.error(traceback.format_exc())
            update_job_error(job_id, "PROCESSING_FAILED", str(e))

        finally:
            # Cleanup is handled by TemporaryDirectory context manager
            pass

    end_time_job = time.time()
    logger.info(
        f"✅ Job {job_id} took {end_time_job - job_start_time:.2f}s (status: done)"
    )
