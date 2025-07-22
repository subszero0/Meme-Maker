#!/usr/bin/env python3
"""
Fix for job processing timeout issue at 40% completion.
This script increases timeout values in the staging environment.
"""

import os
import re
import shutil
from datetime import datetime

def print_status(message):
    print(f"\033[1;34m{message}\033[0m")

def print_success(message):
    print(f"\033[1;32m✅ {message}\033[0m")

def print_error(message):
    print(f"\033[1;31m❌ {message}\033[0m")

def print_warning(message):
    print(f"\033[1;33m⚠️  {message}\033[0m")

def backup_file(file_path):
    """Create a backup of the file"""
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print_success(f"Backup created: {backup_path}")
    return backup_path

def update_async_processor_timeout():
    """Update AsyncVideoProcessor timeout from 300s to 900s (15 minutes)"""
    file_path = "worker/async_video_processor.py"
    
    if not os.path.exists(file_path):
        print_error(f"File not found: {file_path}")
        return False
    
    backup_file(file_path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update the default timeout from 300 to 900 seconds
    old_pattern = r'def __init__\(\s*self, max_concurrent_jobs: int = 5, batch_size: int = 10, timeout: int = 300\s*\)'
    new_replacement = 'def __init__(\n        self, max_concurrent_jobs: int = 5, batch_size: int = 10, timeout: int = 900\n    )'
    
    if re.search(old_pattern, content):
        content = re.sub(old_pattern, new_replacement, content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print_success(f"Updated {file_path}: timeout 300s → 900s (15 minutes)")
        return True
    else:
        print_warning(f"Pattern not found in {file_path}, manual update needed")
        return False

def update_ytdlp_socket_timeouts():
    """Update yt-dlp socket timeouts for better reliability"""
    file_path = "worker/utils/ytdlp_options.py"
    
    if not os.path.exists(file_path):
        print_error(f"File not found: {file_path}")
        return False
    
    backup_file(file_path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update socket timeouts from 30/45/60 to 90/120/180
    content = re.sub(r'"socket_timeout": 30,', '"socket_timeout": 90,', content)
    content = re.sub(r'"socket_timeout": 45,', '"socket_timeout": 120,', content)
    content = re.sub(r'"socket_timeout": 60,', '"socket_timeout": 180,', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print_success(f"Updated {file_path}: increased socket timeouts")
    return True

def update_worker_redis_timeout():
    """Update worker Redis connection timeout"""
    file_path = "worker/main.py"
    
    if not os.path.exists(file_path):
        print_error(f"File not found: {file_path}")
        return False
    
    backup_file(file_path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update Redis timeouts from 10s to 30s
    content = re.sub(r'socket_connect_timeout=10,', 'socket_connect_timeout=30,', content)
    content = re.sub(r'socket_timeout=10,', 'socket_timeout=30,', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print_success(f"Updated {file_path}: Redis timeout 10s → 30s")
    return True

def create_staging_timeout_config():
    """Create staging-specific timeout configuration"""
    config_content = """# Staging Timeout Configuration
# Increased timeouts for better job completion rates

# Video Processing Timeouts
VIDEO_PROCESSING_TIMEOUT = 900  # 15 minutes (up from 5 minutes)
DOWNLOAD_TIMEOUT = 300          # 5 minutes for downloads
TRIM_TIMEOUT = 180             # 3 minutes for trimming

# Network Timeouts  
SOCKET_TIMEOUT = 90            # 90 seconds for socket operations
REDIS_TIMEOUT = 30             # 30 seconds for Redis operations

# Job Processing
MAX_RETRY_ATTEMPTS = 3         # Retry failed jobs 3 times
RETRY_DELAY = 60              # Wait 60 seconds between retries

# Progress Tracking
PROGRESS_UPDATE_INTERVAL = 5   # Update progress every 5 seconds
"""
    
    os.makedirs("config", exist_ok=True)
    config_file = "config/staging_timeouts.py"
    
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print_success(f"Created staging timeout configuration: {config_file}")

def main():
    print_status("🔧 FIXING JOB PROCESSING TIMEOUT ISSUES...")
    print_status("========================================")
    
    print_status("Step 1: Updating AsyncVideoProcessor timeout...")
    update_async_processor_timeout()
    
    print_status("Step 2: Updating yt-dlp socket timeouts...")
    update_ytdlp_socket_timeouts()
    
    print_status("Step 3: Updating worker Redis timeouts...")
    update_worker_redis_timeout()
    
    print_status("Step 4: Creating staging timeout configuration...")
    create_staging_timeout_config()
    
    print_status("Step 5: Summary of changes...")
    print("📊 Timeout Changes Summary:")
    print("==========================")
    print("• Video Processing: 300s → 900s (15 minutes)")
    print("• Socket Timeouts: 30/45/60s → 90/120/180s")
    print("• Redis Timeouts: 10s → 30s")
    print("• Added staging timeout configuration")
    
    print("")
    print_warning("⚠️  IMPORTANT: Restart containers after timeout fixes!")
    print("Run these commands on the server:")
    print("1. docker-compose -f docker-compose.yaml -f docker-compose.staging.monitoring.yml --env-file .env.monitoring.staging restart backend worker")
    print("2. docker-compose -f docker-compose.yaml -f docker-compose.staging.monitoring.yml --env-file .env.monitoring.staging logs -f worker")
    
    print("")
    print_success("🎉 Timeout fixes applied!")
    print("Jobs should now complete beyond 40% with longer processing times.")

if __name__ == "__main__":
    main() 