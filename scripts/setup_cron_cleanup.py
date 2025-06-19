#!/usr/bin/env python3
"""
Setup Cron Jobs for Automated Storage Management
Configures cron jobs for cleanup and monitoring tasks
"""
import os
import sys
import subprocess
from pathlib import Path


def setup_cron_jobs():
    """Setup automated cron jobs for storage management"""
    
    # Define cron jobs
    cron_jobs = [
        # Daily cleanup at 2 AM (24 hour retention)
        "0 2 * * * /usr/bin/python3 /app/scripts/cleanup_old_files.py --max-age-hours 24 >> /var/log/cleanup.log 2>&1",
        
        # Hourly disk usage check
        "0 * * * * /usr/bin/python3 /app/scripts/cleanup_old_files.py --stats-only --warning-threshold 80 >> /var/log/disk_usage.log 2>&1",
        
        # Weekly retention policy (7 days) for old files
        "0 3 * * 0 /usr/bin/python3 /app/scripts/cleanup_old_files.py --max-age-hours 168 >> /var/log/weekly_cleanup.log 2>&1"
    ]
    
    print("🔧 Setting up cron jobs for automated storage management...")
    
    # Create log directory
    log_dir = Path("/var/log")
    log_dir.mkdir(exist_ok=True)
    
    # Get current crontab
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        current_crontab = result.stdout if result.returncode == 0 else ""
    except Exception:
        current_crontab = ""
    
    # Add new jobs if they don't exist
    new_crontab = current_crontab
    
    for job in cron_jobs:
        if job not in current_crontab:
            new_crontab += f"\n{job}"
            print(f"➕ Added: {job}")
        else:
            print(f"✅ Already exists: {job}")
    
    # Write updated crontab
    if new_crontab != current_crontab:
        try:
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_crontab)
            
            if process.returncode == 0:
                print("✅ Cron jobs installed successfully")
            else:
                print("❌ Failed to install cron jobs")
                
        except Exception as e:
            print(f"❌ Error setting up cron jobs: {e}")
    else:
        print("✅ All cron jobs already configured")
    
    # Create log rotation config
    create_logrotate_config()


def create_logrotate_config():
    """Create log rotation configuration for cleanup logs"""
    logrotate_config = """
/var/log/cleanup.log /var/log/disk_usage.log /var/log/weekly_cleanup.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
"""
    
    logrotate_file = Path("/etc/logrotate.d/meme-maker-cleanup")
    
    try:
        with open(logrotate_file, 'w') as f:
            f.write(logrotate_config)
        print(f"✅ Log rotation configured: {logrotate_file}")
    except Exception as e:
        print(f"⚠️  Could not create log rotation config: {e}")


def remove_cron_jobs():
    """Remove all meme-maker related cron jobs"""
    print("🗑️  Removing meme-maker cron jobs...")
    
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode != 0:
            print("No crontab found")
            return
        
        current_crontab = result.stdout
        
        # Filter out meme-maker related jobs
        filtered_lines = []
        for line in current_crontab.split('\n'):
            if '/app/scripts/cleanup_old_files.py' not in line:
                filtered_lines.append(line)
        
        new_crontab = '\n'.join(filtered_lines)
        
        # Write filtered crontab
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_crontab)
        
        if process.returncode == 0:
            print("✅ Cron jobs removed successfully")
        else:
            print("❌ Failed to remove cron jobs")
            
    except Exception as e:
        print(f"❌ Error removing cron jobs: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup or remove cron jobs for storage management')
    parser.add_argument('--remove', action='store_true', help='Remove cron jobs instead of setting them up')
    
    args = parser.parse_args()
    
    if args.remove:
        remove_cron_jobs()
    else:
        setup_cron_jobs()


if __name__ == "__main__":
    main() 