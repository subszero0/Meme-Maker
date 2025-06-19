#!/usr/bin/env python3
"""
Automated cleanup script for Meme Maker local storage.
Removes old files and provides storage monitoring capabilities.
"""

import os
import sys
import time
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import shutil

# Add backend path for imports
sys.path.append('/app/backend')

try:
    from app.config import settings
    BACKEND_AVAILABLE = True
except ImportError:
    BACKEND_AVAILABLE = False
    # Fallback configuration
    CLIPS_DIR = os.getenv('CLIPS_DIR', '/app/clips')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/mememaker-cleanup.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)


def get_clips_directory() -> Path:
    """Get clips directory from configuration or environment"""
    if BACKEND_AVAILABLE:
        return Path(settings.clips_dir)
    else:
        return Path(CLIPS_DIR)


def get_directory_size(path: Path) -> int:
    """Calculate total size of directory in bytes"""
    total_size = 0
    try:
        for file_path in path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
    except (OSError, PermissionError) as e:
        logger.warning(f"Error calculating size for {path}: {e}")
    return total_size


def get_disk_usage(path: Path) -> Dict[str, Any]:
    """Get disk usage statistics for the given path"""
    try:
        disk_usage = shutil.disk_usage(path)
        return {
            "total_bytes": disk_usage.total,
            "used_bytes": disk_usage.used,
            "free_bytes": disk_usage.free,
            "used_percentage": round((disk_usage.used / disk_usage.total) * 100, 2),
            "free_percentage": round((disk_usage.free / disk_usage.total) * 100, 2)
        }
    except (OSError, PermissionError) as e:
        logger.error(f"Error getting disk usage for {path}: {e}")
        return {}


def cleanup_old_files(
    clips_dir: Path,
    max_age_hours: int = 24,
    dry_run: bool = False,
    size_threshold_gb: float = None
) -> Dict[str, Any]:
    """
    Clean up old files based on age and optionally size thresholds.
    
    Args:
        clips_dir: Base directory containing clips
        max_age_hours: Maximum age of files to keep (default: 24 hours)
        dry_run: If True, only report what would be deleted
        size_threshold_gb: If set, force cleanup when storage exceeds this size
        
    Returns:
        Dictionary with cleanup statistics
    """
    if not clips_dir.exists():
        logger.warning(f"Clips directory does not exist: {clips_dir}")
        return {"error": "Directory not found"}
    
    cutoff_time = time.time() - (max_age_hours * 3600)
    
    stats = {
        "files_processed": 0,
        "files_deleted": 0,
        "bytes_deleted": 0,
        "directories_cleaned": 0,
        "errors": 0,
        "dry_run": dry_run,
        "max_age_hours": max_age_hours
    }
    
    # Get current storage size
    current_size_bytes = get_directory_size(clips_dir)
    current_size_gb = current_size_bytes / (1024**3)
    
    logger.info(f"Starting cleanup - Current storage: {current_size_gb:.2f} GB")
    
    # Force cleanup if size threshold exceeded
    force_cleanup = size_threshold_gb and current_size_gb > size_threshold_gb
    if force_cleanup:
        logger.warning(f"Storage size ({current_size_gb:.2f} GB) exceeds threshold ({size_threshold_gb} GB). Forcing cleanup.")
        # Reduce max_age_hours for aggressive cleanup
        max_age_hours = max(1, max_age_hours // 2)
        cutoff_time = time.time() - (max_age_hours * 3600)
    
    # Process all files recursively
    for file_path in clips_dir.rglob('*'):
        if file_path.is_file():
            stats["files_processed"] += 1
            
            try:
                file_mtime = file_path.stat().st_mtime
                file_size = file_path.stat().st_size
                
                # Check if file is old enough to delete
                if file_mtime < cutoff_time:
                    if dry_run:
                        logger.info(f"[DRY RUN] Would delete: {file_path} ({file_size} bytes)")
                    else:
                        logger.info(f"Deleting old file: {file_path} ({file_size} bytes)")
                        file_path.unlink()
                    
                    stats["files_deleted"] += 1
                    stats["bytes_deleted"] += file_size
                
            except (OSError, PermissionError) as e:
                logger.error(f"Error processing file {file_path}: {e}")
                stats["errors"] += 1
    
    # Clean up empty directories
    for dir_path in clips_dir.rglob('*'):
        if dir_path.is_dir() and dir_path != clips_dir:
            try:
                # Check if directory is empty
                if not any(dir_path.iterdir()):
                    if dry_run:
                        logger.info(f"[DRY RUN] Would remove empty directory: {dir_path}")
                    else:
                        logger.info(f"Removing empty directory: {dir_path}")
                        dir_path.rmdir()
                    stats["directories_cleaned"] += 1
            except (OSError, PermissionError) as e:
                logger.error(f"Error removing directory {dir_path}: {e}")
                stats["errors"] += 1
    
    # Log cleanup summary
    deleted_mb = stats["bytes_deleted"] / (1024**2)
    logger.info(f"Cleanup completed: {stats['files_deleted']} files deleted, "
                f"{deleted_mb:.2f} MB freed, {stats['directories_cleaned']} empty dirs removed")
    
    if stats["errors"] > 0:
        logger.warning(f"Cleanup completed with {stats['errors']} errors")
    
    return stats


def get_storage_report(clips_dir: Path) -> Dict[str, Any]:
    """Generate comprehensive storage report"""
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "clips_directory": str(clips_dir),
        "directory_exists": clips_dir.exists()
    }
    
    if not clips_dir.exists():
        return report
    
    # File statistics
    file_count = 0
    total_size_bytes = 0
    file_types = {}
    age_distribution = {"0-1h": 0, "1-6h": 0, "6-24h": 0, "1-7d": 0, "7d+": 0}
    
    current_time = time.time()
    
    for file_path in clips_dir.rglob('*'):
        if file_path.is_file():
            file_count += 1
            file_size = file_path.stat().st_size
            total_size_bytes += file_size
            
            # Track file types
            suffix = file_path.suffix.lower()
            file_types[suffix] = file_types.get(suffix, 0) + 1
            
            # Track age distribution
            age_hours = (current_time - file_path.stat().st_mtime) / 3600
            if age_hours < 1:
                age_distribution["0-1h"] += 1
            elif age_hours < 6:
                age_distribution["1-6h"] += 1
            elif age_hours < 24:
                age_distribution["6-24h"] += 1
            elif age_hours < 168:  # 7 days
                age_distribution["1-7d"] += 1
            else:
                age_distribution["7d+"] += 1
    
    # Directory structure
    date_dirs = []
    for item in clips_dir.iterdir():
        if item.is_dir() and item.name.match(r'\d{4}-\d{2}-\d{2}'):
            date_dirs.append(item.name)
    
    report.update({
        "file_count": file_count,
        "total_size_bytes": total_size_bytes,
        "total_size_mb": round(total_size_bytes / (1024**2), 2),
        "total_size_gb": round(total_size_bytes / (1024**3), 3),
        "file_types": file_types,
        "age_distribution": age_distribution,
        "date_directories": sorted(date_dirs, reverse=True)[:10],  # Last 10 days
        "disk_usage": get_disk_usage(clips_dir)
    })
    
    return report


def monitor_storage_capacity(clips_dir: Path, warning_threshold: float = 80.0, critical_threshold: float = 90.0) -> Dict[str, Any]:
    """Monitor storage capacity and return alerts if thresholds exceeded"""
    disk_usage = get_disk_usage(clips_dir)
    
    alerts = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "ok",
        "warnings": [],
        "critical": [],
        "disk_usage": disk_usage
    }
    
    if not disk_usage:
        alerts["critical"].append("Unable to determine disk usage")
        alerts["status"] = "error"
        return alerts
    
    used_percentage = disk_usage["used_percentage"]
    
    if used_percentage >= critical_threshold:
        alerts["critical"].append(f"Disk usage critical: {used_percentage}% (threshold: {critical_threshold}%)")
        alerts["status"] = "critical"
    elif used_percentage >= warning_threshold:
        alerts["warnings"].append(f"Disk usage warning: {used_percentage}% (threshold: {warning_threshold}%)")
        alerts["status"] = "warning"
    
    # Check clips directory size
    clips_size_bytes = get_directory_size(clips_dir)
    clips_size_gb = clips_size_bytes / (1024**3)
    
    # Alert if clips directory is taking up more than expected space
    if clips_size_gb > 10:  # More than 10GB seems excessive for clips
        alerts["warnings"].append(f"Clips directory unusually large: {clips_size_gb:.2f} GB")
        if alerts["status"] == "ok":
            alerts["status"] = "warning"
    
    alerts["clips_size_gb"] = round(clips_size_gb, 2)
    
    return alerts


def main():
    """Main entry point for cleanup script"""
    parser = argparse.ArgumentParser(description="Meme Maker Storage Cleanup and Monitoring")
    parser.add_argument("--max-age", type=int, default=24, help="Maximum age of files to keep (hours)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without actually deleting")
    parser.add_argument("--report", action="store_true", help="Generate storage report")
    parser.add_argument("--monitor", action="store_true", help="Monitor storage capacity")
    parser.add_argument("--size-threshold", type=float, help="Force cleanup if storage exceeds this size (GB)")
    parser.add_argument("--warning-threshold", type=float, default=80.0, help="Disk usage warning threshold (percentage)")
    parser.add_argument("--critical-threshold", type=float, default=90.0, help="Disk usage critical threshold (percentage)")
    
    args = parser.parse_args()
    
    clips_dir = get_clips_directory()
    
    try:
        if args.report:
            logger.info("Generating storage report...")
            report = get_storage_report(clips_dir)
            print("\n=== STORAGE REPORT ===")
            print(f"Directory: {report['clips_directory']}")
            print(f"Files: {report.get('file_count', 0)}")
            print(f"Total Size: {report.get('total_size_gb', 0)} GB")
            print(f"Disk Usage: {report.get('disk_usage', {}).get('used_percentage', 'Unknown')}%")
            print(f"File Types: {report.get('file_types', {})}")
            print(f"Age Distribution: {report.get('age_distribution', {})}")
            
        if args.monitor:
            logger.info("Monitoring storage capacity...")
            alerts = monitor_storage_capacity(clips_dir, args.warning_threshold, args.critical_threshold)
            print(f"\n=== STORAGE MONITORING ===")
            print(f"Status: {alerts['status'].upper()}")
            print(f"Clips Size: {alerts.get('clips_size_gb', 0)} GB")
            print(f"Disk Usage: {alerts.get('disk_usage', {}).get('used_percentage', 'Unknown')}%")
            
            if alerts['warnings']:
                print("Warnings:")
                for warning in alerts['warnings']:
                    print(f"  - {warning}")
            
            if alerts['critical']:
                print("Critical Issues:")
                for critical in alerts['critical']:
                    print(f"  - {critical}")
                return 1  # Exit with error code for critical issues
        
        # Always run cleanup unless only report/monitor requested
        if not (args.report or args.monitor) or args.size_threshold:
            logger.info(f"Starting cleanup (max age: {args.max_age} hours, dry run: {args.dry_run})")
            stats = cleanup_old_files(
                clips_dir, 
                max_age_hours=args.max_age,
                dry_run=args.dry_run,
                size_threshold_gb=args.size_threshold
            )
            
            print(f"\n=== CLEANUP RESULTS ===")
            print(f"Files processed: {stats['files_processed']}")
            print(f"Files deleted: {stats['files_deleted']}")
            print(f"Space freed: {stats['bytes_deleted'] / (1024**2):.2f} MB")
            print(f"Directories cleaned: {stats['directories_cleaned']}")
            print(f"Errors: {stats['errors']}")
            
            if stats['errors'] > 0:
                return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Cleanup script failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main()) 