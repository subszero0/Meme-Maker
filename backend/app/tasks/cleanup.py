"""
Background cleanup tasks for automated maintenance.
Handles cleanup of temporary files, expired jobs, and storage optimization.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import shutil
import os

from fastapi import BackgroundTasks
from ..config.configuration import get_settings
from ..constants import StorageConfig, JobStates
from ..repositories.job_repository import JobRepository
from ..logging.config import get_logger
from ..exceptions import RepositoryError


logger = get_logger(__name__)


class CleanupManager:
    """Manager for background cleanup operations"""
    
    def __init__(self, job_repository: JobRepository):
        self.job_repository = job_repository
        self.settings = get_settings()
        
    async def cleanup_expired_jobs(self) -> Dict[str, int]:
        """
        Clean up expired jobs and their associated data
        
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=self.settings.cleanup_after_hours)
            
            logger.info(f"Starting job cleanup for jobs older than {cutoff_time}")
            
            # Get expired jobs before deletion for file cleanup
            expired_jobs = await self._get_expired_jobs(cutoff_time)
            
            # Clean up associated files
            files_deleted = await self._cleanup_job_files(expired_jobs)
            
            # Delete job records
            jobs_deleted = await self.job_repository.cleanup_jobs_before(cutoff_time)
            
            stats = {
                'jobs_deleted': jobs_deleted,
                'files_deleted': files_deleted,
                'cutoff_time': cutoff_time.isoformat()
            }
            
            logger.info(f"Job cleanup completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Job cleanup failed: {str(e)}", exc_info=True)
            raise
    
    async def cleanup_temporary_files(self, max_age_hours: int = 24) -> Dict[str, int]:
        """
        Clean up temporary files older than specified age
        
        Args:
            max_age_hours: Maximum age in hours for temporary files
            
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            temp_dirs = [
                Path(StorageConfig.TEMP_DIR),
                Path(self.settings.clips_dir) / "temp",
                Path("/tmp/video_processing")
            ]
            
            total_files_deleted = 0
            total_size_freed = 0
            
            for temp_dir in temp_dirs:
                if temp_dir.exists():
                    result = await self._cleanup_directory(temp_dir, cutoff_time)
                    total_files_deleted += result['files_deleted']
                    total_size_freed += result['size_freed']
            
            stats = {
                'files_deleted': total_files_deleted,
                'size_freed_mb': round(total_size_freed / (1024 * 1024), 2),
                'directories_scanned': len([d for d in temp_dirs if d.exists()]),
                'cutoff_time': cutoff_time.isoformat()
            }
            
            logger.info(f"Temporary file cleanup completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Temporary file cleanup failed: {str(e)}", exc_info=True)
            raise
    
    async def cleanup_storage_directory(self) -> Dict[str, int]:
        """
        Clean up the main storage directory using configured retention policy
        
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            storage_path = Path(self.settings.clips_dir)
            
            if not storage_path.exists():
                logger.warning(f"Storage directory does not exist: {storage_path}")
                return {'files_deleted': 0, 'size_freed_mb': 0}
            
            cutoff_time = datetime.now() - timedelta(hours=self.settings.cleanup_after_hours)
            
            result = await self._cleanup_directory(storage_path, cutoff_time)
            
            # Also clean up empty date directories
            empty_dirs_removed = await self._remove_empty_directories(storage_path)
            
            stats = {
                'files_deleted': result['files_deleted'],
                'size_freed_mb': round(result['size_freed'] / (1024 * 1024), 2),
                'empty_dirs_removed': empty_dirs_removed,
                'cutoff_time': cutoff_time.isoformat()
            }
            
            logger.info(f"Storage cleanup completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Storage cleanup failed: {str(e)}", exc_info=True)
            raise
    
    async def optimize_storage(self) -> Dict[str, any]:
        """
        Optimize storage by removing duplicates and compressing old files
        
        Returns:
            Dictionary with optimization statistics
        """
        try:
            storage_path = Path(self.settings.clips_dir)
            
            if not storage_path.exists():
                return {'duplicates_removed': 0, 'files_compressed': 0}
            
            # Find and remove duplicate files
            duplicates_removed = await self._remove_duplicate_files(storage_path)
            
            # Get storage usage statistics
            usage_stats = await self._get_storage_usage(storage_path)
            
            stats = {
                'duplicates_removed': duplicates_removed,
                'total_files': usage_stats['file_count'],
                'total_size_mb': usage_stats['total_size_mb'],
                'largest_file_mb': usage_stats['largest_file_mb']
            }
            
            logger.info(f"Storage optimization completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Storage optimization failed: {str(e)}", exc_info=True)
            raise
    
    async def _get_expired_jobs(self, cutoff_time: datetime) -> List[Dict]:
        """Get list of expired jobs for file cleanup"""
        try:
            # This would need to be implemented based on job repository capabilities
            # For now, return empty list as placeholder
            return []
        except Exception as e:
            logger.error(f"Failed to get expired jobs: {str(e)}")
            return []
    
    async def _cleanup_job_files(self, jobs: List[Dict]) -> int:
        """Clean up files associated with specific jobs"""
        files_deleted = 0
        
        for job in jobs:
            try:
                # Clean up job-specific files if they exist
                job_id = job.get('id')
                if job_id:
                    job_files = await self._find_job_files(job_id)
                    for file_path in job_files:
                        if await self._delete_file_safe(file_path):
                            files_deleted += 1
                            
            except Exception as e:
                logger.error(f"Failed to cleanup files for job {job.get('id')}: {str(e)}")
        
        return files_deleted
    
    async def _cleanup_directory(self, directory: Path, cutoff_time: datetime) -> Dict[str, int]:
        """Clean up files in a directory older than cutoff time"""
        files_deleted = 0
        size_freed = 0
        
        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    try:
                        # Check file modification time
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        
                        if mtime < cutoff_time:
                            file_size = file_path.stat().st_size
                            
                            if await self._delete_file_safe(file_path):
                                files_deleted += 1
                                size_freed += file_size
                                logger.debug(f"Deleted old file: {file_path}")
                                
                    except Exception as e:
                        logger.warning(f"Failed to process file {file_path}: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Failed to cleanup directory {directory}: {str(e)}")
        
        return {'files_deleted': files_deleted, 'size_freed': size_freed}
    
    async def _remove_empty_directories(self, root_path: Path) -> int:
        """Remove empty directories recursively"""
        removed_count = 0
        
        try:
            # Walk directories bottom-up to handle nested empty directories
            for dir_path in sorted(root_path.rglob("*"), key=lambda p: len(p.parts), reverse=True):
                if dir_path.is_dir() and dir_path != root_path:
                    try:
                        # Check if directory is empty
                        if not any(dir_path.iterdir()):
                            dir_path.rmdir()
                            removed_count += 1
                            logger.debug(f"Removed empty directory: {dir_path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove directory {dir_path}: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Failed to remove empty directories: {str(e)}")
        
        return removed_count
    
    async def _find_job_files(self, job_id: str) -> List[Path]:
        """Find all files associated with a specific job"""
        job_files = []
        
        try:
            storage_path = Path(self.settings.clips_dir)
            
            # Search for files with job_id in name
            for file_path in storage_path.rglob(f"*{job_id}*"):
                if file_path.is_file():
                    job_files.append(file_path)
                    
        except Exception as e:
            logger.error(f"Failed to find files for job {job_id}: {str(e)}")
        
        return job_files
    
    async def _delete_file_safe(self, file_path: Path) -> bool:
        """Safely delete a file with error handling"""
        try:
            if file_path.exists():
                file_path.unlink()
                return True
        except Exception as e:
            logger.warning(f"Failed to delete file {file_path}: {str(e)}")
        
        return False
    
    async def _remove_duplicate_files(self, directory: Path) -> int:
        """Remove duplicate files based on content hash"""
        # This is a placeholder for duplicate detection logic
        # In a real implementation, you'd hash files and compare
        return 0
    
    async def _get_storage_usage(self, directory: Path) -> Dict[str, any]:
        """Get storage usage statistics"""
        try:
            total_size = 0
            file_count = 0
            largest_file = 0
            
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    file_count += 1
                    
                    if file_size > largest_file:
                        largest_file = file_size
            
            return {
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'file_count': file_count,
                'largest_file_mb': round(largest_file / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage usage: {str(e)}")
            return {'total_size_mb': 0, 'file_count': 0, 'largest_file_mb': 0}


# Background task functions for FastAPI
async def schedule_cleanup_job(background_tasks: BackgroundTasks, job_repository: JobRepository):
    """Schedule a cleanup job to run in the background"""
    cleanup_manager = CleanupManager(job_repository)
    background_tasks.add_task(cleanup_manager.cleanup_expired_jobs)


async def schedule_temp_cleanup(background_tasks: BackgroundTasks, job_repository: JobRepository):
    """Schedule temporary file cleanup"""
    cleanup_manager = CleanupManager(job_repository)
    background_tasks.add_task(cleanup_manager.cleanup_temporary_files)


async def schedule_storage_optimization(background_tasks: BackgroundTasks, job_repository: JobRepository):
    """Schedule storage optimization"""
    cleanup_manager = CleanupManager(job_repository)
    background_tasks.add_task(cleanup_manager.optimize_storage)


# Periodic cleanup scheduler
class PeriodicCleanupScheduler:
    """Scheduler for running cleanup tasks periodically"""
    
    def __init__(self, job_repository: JobRepository):
        self.cleanup_manager = CleanupManager(job_repository)
        self.is_running = False
        
    async def start_periodic_cleanup(self, interval_hours: int = 6):
        """Start periodic cleanup tasks"""
        if self.is_running:
            logger.warning("Periodic cleanup is already running")
            return
            
        self.is_running = True
        logger.info(f"Starting periodic cleanup every {interval_hours} hours")
        
        try:
            while self.is_running:
                try:
                    # Run cleanup tasks
                    await self.cleanup_manager.cleanup_expired_jobs()
                    await self.cleanup_manager.cleanup_temporary_files()
                    
                    # Wait for next interval
                    await asyncio.sleep(interval_hours * 3600)
                    
                except Exception as e:
                    logger.error(f"Periodic cleanup error: {str(e)}", exc_info=True)
                    # Continue running even if one cycle fails
                    await asyncio.sleep(300)  # Wait 5 minutes before retrying
                    
        except asyncio.CancelledError:
            logger.info("Periodic cleanup cancelled")
        finally:
            self.is_running = False
    
    def stop_periodic_cleanup(self):
        """Stop periodic cleanup tasks"""
        self.is_running = False
        logger.info("Stopping periodic cleanup") 