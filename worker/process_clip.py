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
from app.metrics import clip_job_latency_seconds, clip_jobs_inflight

logger = logging.getLogger(__name__)


def update_job_progress(job_id: str, progress: int, status: Optional[str] = None):
    """Update job progress and status in Redis"""
    try:
        job_key = f"job:{job_id}"
        update_data = {"progress": progress}
        if status:
            update_data["status"] = status
        redis.hset(job_key, mapping=update_data)
        redis.expire(job_key, 3600)  # 1 hour expiry
    except Exception as e:
        logger.error(f"Failed to update job progress for {job_id}: {e}")


def update_job_error(job_id: str, error_code: str, error_message: str):
    """Update job with error status and details"""
    try:
        job_key = f"job:{job_id}"
        redis.hset(job_key, mapping={
            "status": JobStatus.error.value,
            "error_code": error_code,
            "error_message": error_message[:500],  # Truncate long error messages
            "progress": None
        })
        redis.expire(job_key, 3600)
    except Exception as e:
        logger.error(f"Failed to update job error for {job_id}: {e}")


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
    # Start timing and increment inflight gauge
    start_time = time.monotonic()
    clip_jobs_inflight.inc()
    
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
        ydl_opts = {
            'outtmpl': str(source_file),
            'format': 'best[height<=1080]',
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
                # Handle playlist URLs
                if 'entries' in info and info['entries']:
                    info = info['entries'][0]
            except Exception as e:
                raise Exception(f"YTDLP_FAIL: {str(e)}")
        
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
        clip_job_latency_seconds.labels(status=job_status).observe(job_latency)
        
        # Decrement inflight gauge
        clip_jobs_inflight.dec() 