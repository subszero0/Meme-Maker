#!/usr/bin/env python3
"""
Main worker process for video clipping jobs
Continuously polls Redis for queued jobs and processes them
"""

import sys
import time
import logging
import traceback
from datetime import datetime, timezone

# Add backend to path for imports
import os
backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
sys.path.append(backend_path)

# Import backend dependencies
from app import redis, settings
from app.models import JobStatus

# Import worker functionality
from process_clip import process_clip

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_queued_jobs():
    """Get all jobs with 'queued' status from Redis"""
    try:
        # Scan for all job keys
        cursor = 0
        jobs = []
        while True:
            cursor, keys = redis.scan(cursor, match="job:*", count=100)
            for key in keys:
                job_data = redis.hgetall(key)
                if job_data and job_data.get(b'status', b'').decode() == 'queued':
                    # Decode the job data
                    decoded_job = {k.decode(): v.decode() for k, v in job_data.items()}
                    jobs.append({
                        'id': decoded_job['id'],
                        'url': decoded_job['url'],
                        'in_ts': float(decoded_job['in_ts']),
                        'out_ts': float(decoded_job['out_ts']),
                        'created_at': decoded_job['created_at'],
                        'format_id': decoded_job.get('format_id') if decoded_job.get('format_id') != 'None' else None
                    })
            if cursor == 0:
                break
        
        # Sort by created_at (oldest first)
        jobs.sort(key=lambda x: x['created_at'])
        return jobs
        
    except Exception as e:
        logger.error(f"Error getting queued jobs: {e}")
        return []

def mark_job_as_working(job_id: str):
    """Mark a job as being worked on"""
    try:
        job_key = f"job:{job_id}"
        redis.hset(job_key, mapping={
            "status": JobStatus.working.value,
            "progress": 0,
                            "started_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        })
        redis.expire(job_key, 3600)  # 1 hour expiry
        return True
    except Exception as e:
        logger.error(f"Failed to mark job {job_id} as working: {e}")
        return False

def main():
    """Main worker loop"""
    logger.info("🚀 Worker starting up...")
    logger.info(f"📍 Redis URL: {settings.redis_url}")
    logger.info(f"🐳 Environment: {getattr(settings, 'environment', 'development')}")
    
    # Test Redis connection
    try:
        redis.ping()
        logger.info("✅ Redis connection successful")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        sys.exit(1)
    
    poll_interval = 2  # seconds
    logger.info(f"⏰ Starting job polling (interval: {poll_interval}s)")
    
    while True:
        try:
            # Get queued jobs
            queued_jobs = get_queued_jobs()
            
            if queued_jobs:
                logger.info(f"📋 Found {len(queued_jobs)} queued job(s)")
                
                for job in queued_jobs:
                    job_id = job['id']
                    logger.info(f"🎬 Processing job {job_id}: {job['url']} [{job['in_ts']}s - {job['out_ts']}s]")
                    
                    # Mark job as working
                    if mark_job_as_working(job_id):
                        try:
                            # Process the job
                            process_clip(
                                job_id=job_id,
                                url=job['url'],
                                in_ts=job['in_ts'],
                                out_ts=job['out_ts'],
                                format_id=job.get('format_id')  # Pass format_id if provided
                            )
                            logger.info(f"✅ Job {job_id} completed successfully")
                            
                        except Exception as e:
                            logger.error(f"❌ Job {job_id} failed: {e}")
                            logger.error(f"📍 Traceback: {traceback.format_exc()}")
                            
                            # Update job with error status
                            try:
                                job_key = f"job:{job_id}"
                                redis.hset(job_key, mapping={
                                    "status": JobStatus.error.value,
                                    "error_code": "PROCESSING_FAILED",
                                    "error_message": str(e)[:500],
                                    "progress": None
                                })
                                redis.expire(job_key, 3600)
                            except Exception as update_error:
                                logger.error(f"Failed to update job error status: {update_error}")
                    else:
                        logger.error(f"❌ Failed to mark job {job_id} as working, skipping...")
            
            # Wait before next poll
            time.sleep(poll_interval)
            
        except KeyboardInterrupt:
            logger.info("🛑 Worker shutdown requested")
            break
        except Exception as e:
            logger.error(f"❌ Unexpected error in main loop: {e}")
            logger.error(f"📍 Traceback: {traceback.format_exc()}")
            time.sleep(poll_interval)

if __name__ == "__main__":
    main() 