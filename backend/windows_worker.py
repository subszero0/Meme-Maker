#!/usr/bin/env python3
"""
Windows-compatible RQ worker using SimpleWorker (no fork required)
This worker polls the Redis queue and processes jobs without using os.fork()
"""

import sys
import time
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add paths for imports
backend_path = Path(__file__).parent
project_root = backend_path.parent
worker_path = project_root / "worker"

# Add both backend and worker to path
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(worker_path))

logger.info(f"✅ Added paths: backend={backend_path}, project_root={project_root}, worker={worker_path}")

try:
    from rq import Worker, Queue
    from app.config.configuration import get_settings
    from app import init_redis
    import redis as redis_module
    
    settings = get_settings()
    logger.info(f"✅ Loaded settings: Redis URL = {settings.redis_url}")
    
except ImportError as e:
    logger.error(f"❌ Failed to import required modules: {e}")
    sys.exit(1)


def create_windows_worker():
    """Create a Windows-compatible RQ worker using standard Worker with proper connection"""
    
    # Initialize Redis connection with proper configuration
    logger.info("🔍 Initializing Redis connection for Windows worker...")
    
    try:
        # Create Redis connection with decode_responses=True for compatibility
        redis_conn = redis_module.Redis.from_url(
            settings.redis_url,
            decode_responses=True,  # This fixes the decode() attribute error
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        
        # Test connection with retries (matching backend pattern)
        for attempt in range(3):
            try:
                result = redis_conn.ping()
                logger.info(f"✅ Redis ping successful on attempt {attempt + 1}: {result}")
                break
            except Exception as retry_e:
                if attempt == 2:  # Last attempt
                    raise retry_e
                logger.info(f"⚠️ Redis ping failed attempt {attempt + 1}: {retry_e}")
                time.sleep(1)
        
        logger.info("✅ Connected to real Redis")
        
        # Create queue
        queue = Queue('clips', connection=redis_conn)
        logger.info("✅ Created 'clips' queue with real Redis")
        
        # Create worker with proper connection
        worker = Worker(['clips'], connection=redis_conn)
        logger.info("✅ Created Worker (Windows-compatible) with real Redis")
        
        return worker, queue
        
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        
        # Fall back to FakeRedis for local development (matching backend pattern)
        try:
            import fakeredis
            from rq import Queue, Worker
            
            logger.info("🔄 Falling back to FakeRedis for local development...")
            
            # Create FakeRedis connection
            fake_redis = fakeredis.FakeRedis(decode_responses=True)
            logger.info("✅ FakeRedis connection created")
            
            # Test fake connection
            fake_redis.ping()
            logger.info("✅ FakeRedis ping successful")
            
            # Create queue with FakeRedis
            queue = Queue('clips', connection=fake_redis)
            logger.info("✅ Created 'clips' queue with FakeRedis")
            
            # Create worker with FakeRedis
            worker = Worker(['clips'], connection=fake_redis)
            logger.info("✅ Created Worker (Windows-compatible) with FakeRedis")
            
            logger.info("⚠️ Using FakeRedis for local development - jobs will work but won't persist between restarts")
            
            return worker, queue
            
        except ImportError:
            logger.error("❌ Both Redis and FakeRedis unavailable - fakeredis not installed")
            raise Exception("Redis connection failed and FakeRedis fallback unavailable")
        except Exception as fake_e:
            logger.error(f"❌ FakeRedis fallback also failed: {fake_e}")
            raise Exception(f"Both Redis and FakeRedis failed: {e}, {fake_e}")


def main():
    """Main function to run the Windows worker"""
    logger.info("🚀 Starting Windows-compatible RQ worker...")
    
    try:
        worker, queue = create_windows_worker()
        logger.info("✅ Worker created successfully")
        
        # Start the worker
        logger.info("🔄 Starting job processing loop...")
        worker.work(with_scheduler=False)  # Disable scheduler for Windows compatibility
        
    except KeyboardInterrupt:
        logger.info("🛑 Worker stopped by user")
    except Exception as e:
        logger.error(f"❌ Worker failed: {e}")
        raise
    finally:
        logger.info("✅ Worker stopped")


if __name__ == "__main__":
    main() 