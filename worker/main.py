#!/usr/bin/env python3
"""
Main worker process for video clipping jobs
Continuously polls Redis for queued jobs and processes them
"""

import sys
import time
import logging
import traceback
import os
from datetime import datetime, timezone

# Configure logging first, before any other imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Correctly set the Python path to find the 'app' module
# This allows us to use the same centralized settings as the backend
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import settings and models from the backend app
try:
    from app.config.configuration import get_settings
    from app.models import JobStatus
    
    # Get settings from the centralized configuration
    worker_settings = get_settings()
    # Manually trigger the print statement to show where env is loaded from
    # This is normally done in the backend's __init__ but we need it here
    from app.config.configuration import env_path, load_dotenv
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"✅ Loaded environment variables from: {env_path}")

except ImportError as e:
    logger.error(f"❌ Could not import from backend 'app'. Ensure PYTHONPATH is set correctly.")
    logger.error(f"Import Error: {e}")
    sys.exit(1)

# Redis connection (will be initialized later)
redis = None

def init_worker_redis():
    """Initialize Redis connection specifically for worker"""
    global redis
    
    logger.info(f"🔍 Initializing Redis connection...")
    logger.info(f"🔍 Redis URL from env: {worker_settings.redis_url}")
    
    try:
        import redis as redis_module
        
        # Try to connect to real Redis
        logger.info(f"🔍 Attempting Redis connection to: {worker_settings.redis_url}")
        redis = redis_module.Redis.from_url(
            worker_settings.redis_url, 
            decode_responses=True, 
            socket_connect_timeout=10,
            socket_timeout=10,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # Test connection with retries
        for attempt in range(3):
            try:
                result = redis.ping()
                logger.info(f"✅ Redis ping successful on attempt {attempt + 1}: {result}")
                return redis
            except Exception as retry_e:
                if attempt == 2:  # Last attempt
                    raise retry_e
                logger.warning(f"⚠️ Redis ping failed attempt {attempt + 1}: {retry_e}")
                time.sleep(1)
                
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        # Fall back to FakeRedis for local development
        try:
            import fakeredis
            redis = fakeredis.FakeRedis(decode_responses=True)
            logger.warning(f"⚠️ Using FakeRedis for local development - caching will work but won't persist")
            return redis
        except ImportError:
            logger.error("❌ Both Redis and FakeRedis unavailable")
            redis = None
            logger.warning("⚠️ Continuing without Redis - caching disabled")
            return None

def get_queued_jobs():
    """Get all jobs with 'queued' status from Redis"""
    if not redis:
        logger.warning("⚠️ Redis not available, returning empty job list")
        return []
        
    try:
        # Scan for all job keys
        cursor = 0
        jobs = []
        while True:
            cursor, keys = redis.scan(cursor, match="job:*", count=100)
            for key in keys:
                job_data = redis.hgetall(key)
                if job_data and job_data.get('status', '') == 'queued':
                    # Data is already decoded due to decode_responses=True
                    jobs.append({
                        'id': job_data['id'],
                        'url': job_data['url'],
                        'in_ts': float(job_data['in_ts']),
                        'out_ts': float(job_data['out_ts']),
                        'created_at': job_data['created_at'],
                        'resolution': job_data.get('resolution'),
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
    if not redis:
        logger.warning("⚠️ Redis not available, cannot mark job as working")
        return False
        
    try:
        job_key = f"job:{job_id}"
        redis.hset(job_key, mapping={
            "status": JobStatus.working,
            "progress": 0,
            "started_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        })
        redis.expire(job_key, 3600)  # 1 hour expiry
        return True
    except Exception as e:
        logger.error(f"Failed to mark job {job_id} as working: {e}")
        return False

def mark_job_as_error(job_id: str, error_message: str):
    """Mark a job as failed with error message"""
    if not redis:
        logger.warning("⚠️ Redis not available, cannot mark job as error")
        return False
        
    try:
        job_key = f"job:{job_id}"
        redis.hset(job_key, mapping={
            "status": JobStatus.error,
            "error_code": "PROCESSING_FAILED",
            "error_message": str(error_message)[:500],
            "progress": None
        })
        redis.expire(job_key, 3600)
        return True
    except Exception as e:
        logger.error(f"Failed to mark job {job_id} as error: {e}")
        return False

def main():
    """Main worker loop"""
    logger.info("🚀 Worker starting up...")
    logger.info(f"📍 Redis URL: {worker_settings.redis_url}")
    logger.info(f"🐳 Environment: {worker_settings.debug}")
    
    # Initialize Redis connection
    redis_instance = init_worker_redis()
    
    if not redis_instance:
        logger.error("❌ Failed to initialize Redis, exiting...")
        sys.exit(1)
    
    logger.info("✅ Redis connection successful")
    
    # Import process_clip only after Redis is working (lazy import to avoid backend issues)
    try:
        logger.info("📦 Loading video processing module...")
        from process_clip import process_clip
        logger.info("✅ Video processing module loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to import process_clip: {e}")
        logger.error(f"📍 Traceback: {traceback.format_exc()}")
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
                                resolution=job.get('resolution'),
                                redis_connection=redis
                            )
                            logger.info(f"✅ Job {job_id} completed successfully")
                            
                        except Exception as e:
                            logger.error(f"❌ Job {job_id} failed: {e}")
                            logger.error(f"📍 Traceback: {traceback.format_exc()}")
                            
                            # Update job with error status
                            mark_job_as_error(job_id, str(e))
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