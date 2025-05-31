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
from redis import Redis
from rq import Worker, Queue

# Import metrics from backend
try:
    sys.path.append('/app')  # Add backend path for imports
    from app.metrics import JOB_DURATION, JOB_FAIL
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    print("Warning: Metrics not available in worker")
    
    # Create dummy context manager
    class DummyMetric:
        def time(self):
            from contextlib import nullcontext
            return nullcontext()
        def labels(self, *args, **kwargs):
            return self
        def inc(self):
            pass
    
    JOB_DURATION = DummyMetric()
    JOB_FAIL = DummyMetric()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection
redis = Redis.from_url(os.environ.get('REDIS_URL', 'redis://redis:6379'))

# MinIO configuration 
MINIO_ENDPOINT = os.environ.get('AWS_ENDPOINT_URL', 'http://minio:9000')
MINIO_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID', 'admin')
MINIO_SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', 'admin12345')
BUCKET_NAME = os.environ.get('S3_BUCKET', 'clips')

# Initialize MinIO client
s3_client = boto3.client(
    's3',
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    region_name='us-east-1'  # Required but not used by MinIO
)


def ensure_bucket_exists():
    """Create the clips bucket if it doesn't exist"""
    try:
        s3_client.head_bucket(Bucket=BUCKET_NAME)
        logger.info(f"Bucket '{BUCKET_NAME}' exists")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            try:
                s3_client.create_bucket(Bucket=BUCKET_NAME)
                logger.info(f"Created bucket '{BUCKET_NAME}'")
            except ClientError as create_error:
                logger.error(f"Failed to create bucket: {create_error}")
                raise
        else:
            logger.error(f"Error checking bucket: {e}")
            raise


def update_job_status(job_id: str, status: str, progress: Optional[int] = None, 
                     error_code: Optional[str] = None, object_key: Optional[str] = None):
    """Update job status in Redis"""
    try:
        job_key = f"job:{job_id}"
        update_data = {"status": status}
        
        if progress is not None:
            update_data["progress"] = progress
        if error_code:
            update_data["error_code"] = error_code
        if object_key:
            update_data["object_key"] = object_key
            
        redis.hset(job_key, mapping=update_data)
        redis.expire(job_key, 3600)  # 1 hour expiry
        logger.info(f"Updated job {job_id}: {status}")
    except Exception as e:
        logger.error(f"Failed to update job status for {job_id}: {e}")


def process_clip(job_id: str, url: str, start_seconds: float, end_seconds: float):
    """
    Process a video clipping job:
    1. Download source with yt-dlp (max 1100M)
    2. Slice clip with FFmpeg using copy codec
    3. Upload to MinIO with content-disposition attachment
    4. Update Redis job status with object key
    """
    with JOB_DURATION.time():
        start_time = time.monotonic()
        temp_dir = None
        
        try:
            logger.info(f"Starting job {job_id}: {url} [{start_seconds}s - {end_seconds}s]")
            
            # Create temporary directory
            temp_dir = Path(tempfile.mkdtemp(prefix=f"clip_{job_id}_"))
            
            # Step 1: Download source with yt-dlp
            update_job_status(job_id, "working", 10)
            
            source_file = temp_dir / f"{job_id}.%(ext)s"
            ydl_opts = {
                'outtmpl': str(source_file),
                'format': 'best[height<=1080]',
                'quiet': True,
                'no_warnings': True,
                'max_filesize': 1100 * 1024 * 1024,  # 1100MB max
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=True)
                    # Handle playlist URLs
                    if 'entries' in info and info['entries']:
                        info = info['entries'][0]
                except Exception as e:
                    update_job_status(job_id, "error", error_code="YTDLP_FAIL")
                    JOB_FAIL.labels(reason="YTDLP_FAIL").inc()
                    raise Exception(f"YTDLP_FAIL: {str(e)}")
            
            # Find the actual downloaded file
            downloaded_files = list(temp_dir.glob(f"{job_id}.*"))
            if not downloaded_files:
                update_job_status(job_id, "error", error_code="YTDLP_FAIL")
                JOB_FAIL.labels(reason="YTDLP_FAIL").inc()
                raise Exception("YTDLP_FAIL: No file downloaded")
            
            source_file = downloaded_files[0]
            logger.info(f"Downloaded: {source_file}")
            
            # Step 2: Clip video with FFmpeg
            update_job_status(job_id, "working", 50)
            
            output_file = temp_dir / f"{job_id}_output.mp4"
            
            # Use copy codec for fast, lossless clipping
            cmd = [
                '/usr/bin/ffmpeg',
                '-i', str(source_file),
                '-ss', str(start_seconds),
                '-to', str(end_seconds),
                '-c', 'copy',
                '-avoid_negative_ts', 'make_zero',
                str(output_file),
                '-y'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                update_job_status(job_id, "error", error_code="FFMPEG_FAIL")
                JOB_FAIL.labels(reason="FFMPEG_FAIL").inc()
                raise Exception(f"FFMPEG_FAIL: {result.stderr}")
            
            logger.info(f"Clipped video: {output_file}")
            
            # Step 3: Upload to MinIO
            update_job_status(job_id, "working", 80)
            
            object_key = f"{job_id}.mp4"
            
            try:
                s3_client.upload_file(
                    str(output_file),
                    BUCKET_NAME,
                    object_key,
                    ExtraArgs={
                        'ContentDisposition': f'attachment; filename="{job_id}.mp4"'
                    }
                )
                logger.info(f"Uploaded to MinIO: {object_key}")
            except Exception as e:
                update_job_status(job_id, "error", error_code="UPLOAD_FAIL")
                JOB_FAIL.labels(reason="UPLOAD_FAIL").inc()
                raise Exception(f"UPLOAD_FAIL: {str(e)}")
            
            # Step 4: Mark job as done with object key
            update_job_status(job_id, "done", 100, object_key=object_key)
            
            duration = time.monotonic() - start_time
            logger.info(f"Job {job_id} completed in {duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            # Error status should already be set in the specific error handlers above
            
        finally:
            # Cleanup temporary files
            if temp_dir and temp_dir.exists():
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temp directory: {temp_dir}")
                except Exception as e:
                    logger.error(f"Failed to cleanup temp directory: {e}")


if __name__ == "__main__":
    # Ensure bucket exists at startup
    ensure_bucket_exists()
    
    # Create RQ worker that can import the function
    queue = Queue("clips", connection=redis)
    worker = Worker([queue], connection=redis)
    
    # Add the function to sys.modules to make it importable
    import sys
    import types
    
    # Create a simple module for our function
    clip_module = types.ModuleType('clip_processor')
    clip_module.process_clip = process_clip
    sys.modules['clip_processor'] = clip_module
    
    logger.info("Starting RQ worker for clip processing...")
    worker.work() 