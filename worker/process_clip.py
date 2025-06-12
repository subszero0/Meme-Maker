import os
import sys
import subprocess
import tempfile
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import boto3
import yt_dlp
from botocore.exceptions import ClientError

# Import from backend app
sys.path.append('/app/backend')
from app import redis, settings
from app.models import JobStatus
# Simplified metrics - avoid Prometheus import issues in worker
# from app.metrics import clip_job_latency_seconds, clip_jobs_inflight

logger = logging.getLogger(__name__)


def update_job_progress(job_id: str, progress: int, status: Optional[str] = None):
    """Update job progress and status in Redis"""
    try:
        job_key = f"job:{job_id}"
        update_data = {"progress": str(progress)}  # Convert to string
        if status:
            update_data["status"] = str(status)  # Convert to string
        redis.hset(job_key, mapping=update_data)
        redis.expire(job_key, 3600)  # 1 hour expiry
        logger.info(f"📊 Job {job_id} progress: {progress}% {f'({status})' if status else ''}")
    except Exception as e:
        logger.error(f"❌ Failed to update job progress for {job_id}: {e}")


def update_job_error(job_id: str, error_code: str, error_message: str):
    """Update job with error status and details"""
    try:
        job_key = f"job:{job_id}"
        # Convert all values to strings to avoid Redis type errors
        mapping_data = {
            "status": str(JobStatus.error.value),
            "error_code": str(error_code),
            "error_message": str(error_message[:500]),  # Truncate long error messages
            "progress": "0"  # Use "0" instead of null for error state
        }
        redis.hset(job_key, mapping=mapping_data)
        redis.expire(job_key, 3600)
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


def process_clip(job_id: str, url: str, in_ts: float, out_ts: float) -> None:
    """
    Process a video clipping job:
    1. Download source with yt-dlp
    2. Slice clip with FFmpeg (smart key-frame fallback)  
    3. Upload to S3 with content-disposition attachment
    4. Update Redis job hash with progress & final URL
    """
    # Start timing 
    start_time = time.monotonic()
    # clip_jobs_inflight.inc()  # Disabled for worker
    
    temp_dir = None
    source_file = None
    output_file = None
    job_status = "error"  # Default to error, will be updated to "done" on success
    
    try:
        logger.info(f"Starting job {job_id}: {url} [{in_ts}s - {out_ts}s]")
        
        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix=f"clip_{job_id}_"))
        
        # Step 1: Download source with yt-dlp
        update_job_progress(job_id, 10, JobStatus.working.value)
        
        source_file = temp_dir / f"{job_id}.%(ext)s"
        
        # Multiple yt-dlp configurations to try in order
        config_attempts = [
            # Attempt 1: Most conservative approach
            {
                'outtmpl': str(source_file),
                'format': 'worst[height<=720]',  # Try lower quality first
                'quiet': True,
                'no_warnings': True,
                'writesubtitles': False,
                'writeautomaticsub': False,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android'],  # Use mobile client
                        'skip': ['dash', 'hls']
                    }
                },
                'http_headers': {
                    'User-Agent': 'com.google.android.youtube/17.31.35 (Linux; U; Android 11) gzip'
                }
            },
            # Attempt 2: Different format selection
            {
                'outtmpl': str(source_file),
                'format': 'best[height<=480]',  # Even lower quality
                'quiet': True,
                'no_warnings': True,
                'writesubtitles': False,
                'writeautomaticsub': False,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15'
                }
            },
            # Attempt 3: Simple fallback
            {
                'outtmpl': str(source_file),
                'format': 'worst',
                'quiet': True,
                'no_warnings': True,
            }
        ]
        
        # Try each configuration
        download_success = False
        last_error = None
        
        for i, ydl_opts in enumerate(config_attempts):
            try:
                logger.info(f"Attempt {i+1}: Trying download with config {i+1}")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    # Handle playlist URLs
                    if 'entries' in info and info['entries']:
                        info = info['entries'][0]
                download_success = True
                logger.info(f"✅ Download successful with config {i+1}")
                break
            except Exception as e:
                last_error = e
                logger.warning(f"❌ Config {i+1} failed: {str(e)}")
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
        logger.info(f"Downloaded: {source_file}")
        
        # Step 2: Probe for nearest key-frame
        update_job_progress(job_id, 20)
        
        nearest_keyframe = find_nearest_keyframe(str(source_file), in_ts)
        needs_reencode = abs(nearest_keyframe - in_ts) > 0.1  # 100ms tolerance
        
        logger.info(f"Key-frame check: in_ts={in_ts}, nearest={nearest_keyframe}, needs_reencode={needs_reencode}")
        
        # Step 3: Clip video with FFmpeg
        update_job_progress(job_id, 30)
        
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
                '-c:v', 'libx264',
                '-preset', 'veryfast',
                '-crf', '18',
                '-c:a', 'copy',
                '-avoid_negative_ts', 'make_zero',
                str(temp_gop_file),
                '-y'
            ]
            
            result = subprocess.run(cmd_gop, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"FFMPEG_FAIL: GOP re-encode failed: {result.stderr}")
            
            update_job_progress(job_id, 50)
            
            # Second pass: copy the rest if needed
            if gop_end < out_ts:
                temp_rest_file = temp_dir / f"{job_id}_rest.mp4"
                cmd_rest = [
                    settings.ffmpeg_path.replace('/usr/local/bin/ffmpeg', '/usr/bin/ffmpeg'),
                    '-i', str(source_file),
                    '-ss', str(gop_end),
                    '-to', str(out_ts),
                    '-c', 'copy',
                    '-avoid_negative_ts', 'make_zero',
                    str(temp_rest_file),
                    '-y'
                ]
                
                result = subprocess.run(cmd_rest, capture_output=True, text=True)
                if result.returncode != 0:
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
                
                result = subprocess.run(cmd_concat, capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"FFMPEG_FAIL: Concatenation failed: {result.stderr}")
            else:
                # Only first GOP needed
                output_file = temp_gop_file
        else:
            # Simple copy without re-encoding
            cmd_copy = [
                settings.ffmpeg_path.replace('/usr/local/bin/ffmpeg', '/usr/bin/ffmpeg'),
                '-i', str(source_file),
                '-ss', str(in_ts),
                '-to', str(out_ts),
                '-c', 'copy',
                '-avoid_negative_ts', 'make_zero',
                str(output_file),
                '-y'
            ]
            
            result = subprocess.run(cmd_copy, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"FFMPEG_FAIL: Copy failed: {result.stderr}")
        
        update_job_progress(job_id, 70)
        
        if not output_file.exists() or output_file.stat().st_size == 0:
            raise Exception("FFMPEG_FAIL: Output file is empty or missing")
        
        logger.info(f"Clipped video: {output_file} ({output_file.stat().st_size} bytes)")
        
        # Step 4: Upload to S3
        update_job_progress(job_id, 90)
        
        s3_client = boto3.client(
            's3',
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
        
        s3_key = f"{job_id}.mp4"
        
        try:
            s3_client.upload_file(
                str(output_file),
                settings.s3_bucket,
                s3_key,
                ExtraArgs={
                    'ContentDisposition': 'attachment',
                    'ContentType': 'video/mp4'
                }
            )
        except ClientError as e:
            raise Exception(f"UPLOAD_FAIL: S3 upload failed: {str(e)}")
        
        # Generate presigned URL (24 hour expiry)
        try:
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.s3_bucket, 'Key': s3_key},
                ExpiresIn=86400  # 24 hours
            )
        except ClientError as e:
            raise Exception(f"UPLOAD_FAIL: Presigned URL generation failed: {str(e)}")
        
        # Step 5: Mark as done
        job_key = f"job:{job_id}"
        redis.hset(job_key, mapping={
            "status": JobStatus.done.value,
            "progress": 100,
            "url": presigned_url,
            "completed_at": datetime.utcnow().isoformat()
        })
        redis.expire(job_key, 3600)
        
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
                import shutil
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