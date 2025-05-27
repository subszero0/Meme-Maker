import os
import yt_dlp
import subprocess
import tempfile
import logging
from pathlib import Path
import boto3
from rq import get_current_job

logger = logging.getLogger(__name__)


def process_video(job_id: str, url: str, start_time: float, end_time: float):
    """
    Process video clipping job
    
    Args:
        job_id: Unique job identifier
        url: Video URL to download
        start_time: Start time in seconds
        end_time: End time in seconds
    
    Returns:
        dict: Result containing download_url or error
    """
    job = get_current_job()
    temp_dir = None
    
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix=f"clip_{job_id}_")
        
        # Update job progress
        job.meta['progress'] = 10
        job.save_meta()
        
        # Download video using yt-dlp
        source_path = os.path.join(temp_dir, "source_video")
        
        ydl_opts = {
            'outtmpl': source_path + '.%(ext)s',
            'format': 'best[height<=1080]',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Handle playlist URLs
            if 'entries' in info and info['entries']:
                info = info['entries'][0]
            
            # Get the actual downloaded file
            downloaded_files = list(Path(temp_dir).glob("source_video.*"))
            if not downloaded_files:
                raise Exception("Failed to download video")
            
            source_file = downloaded_files[0]
        
        job.meta['progress'] = 50
        job.save_meta()
        
        # Clip video using ffmpeg
        output_file = os.path.join(temp_dir, f"clip_{job_id}.mp4")
        
        # Use ffmpeg to clip video
        cmd = [
            'ffmpeg',
            '-i', str(source_file),
            '-ss', str(start_time),
            '-to', str(end_time),
            '-c', 'copy',  # Copy streams without re-encoding when possible
            '-avoid_negative_ts', 'make_zero',
            output_file,
            '-y'  # Overwrite output files
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise Exception(f"Video processing failed: {result.stderr}")
        
        job.meta['progress'] = 80
        job.save_meta()
        
        # Upload to S3 (placeholder for now)
        # In real implementation, upload to S3 and get presigned URL
        download_url = f"http://localhost:8000/download/{job_id}"  # Placeholder
        
        job.meta['progress'] = 100
        job.save_meta()
        
        logger.info(f"Successfully processed job {job_id}")
        
        return {
            'success': True,
            'download_url': download_url,
            'job_id': job_id
        }
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'job_id': job_id
        }
        
    finally:
        # Cleanup temporary files
        if temp_dir and os.path.exists(temp_dir):
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.error(f"Failed to cleanup temp dir {temp_dir}: {str(e)}") 