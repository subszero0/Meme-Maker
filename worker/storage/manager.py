"""
Storage Manager

Handles storage operations with proper error handling and backend abstraction.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass

from ..exceptions import StorageError
from ..progress.tracker import ProgressTracker

# Import from backend app
import sys
sys.path.append('/app/backend')
from app.storage_factory import get_storage_manager as get_backend_storage_manager

logger = logging.getLogger(__name__)


@dataclass
class StorageResult:
    """Result of storage operation"""
    download_url: str
    file_size: int
    sha256: str
    file_path: str
    filename: str


class StorageManager:
    """Manages storage operations with error handling and progress tracking"""
    
    def __init__(self, progress_tracker: ProgressTracker):
        self.progress_tracker = progress_tracker
        self._backend_manager = None
    
    @property
    def backend_manager(self):
        """Lazy-load the backend storage manager"""
        if self._backend_manager is None:
            self._backend_manager = get_backend_storage_manager()
        return self._backend_manager
    
    async def save(self, job_id: str, video_data: bytes, title: str) -> StorageResult:
        """
        Save processed video with atomic operations
        
        Args:
            job_id: Unique job identifier
            video_data: Video file content as bytes
            title: Video title for filename
            
        Returns:
            StorageResult with download URL and metadata
            
        Raises:
            StorageError: If storage operation fails
        """
        try:
            self.progress_tracker.update(87, stage="Reading processed video...")
            logger.info(f"🎬 Preparing to save {len(video_data):,} bytes for job {job_id}")
            
            self.progress_tracker.update(90, stage="Uploading to storage...")
            
            # Use existing backend storage manager with proper async handling
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                storage_result = loop.run_until_complete(
                    self.backend_manager.save(job_id, video_data, title)
                )
            finally:
                loop.close()
            
            self.progress_tracker.update(95, stage="Generating download link...")
            
            # Generate download URL using backend API
            download_url = self.backend_manager.get_download_url(job_id, storage_result["filename"])
            
            result = StorageResult(
                download_url=download_url,
                file_size=storage_result["size"],
                sha256=storage_result["sha256"],
                file_path=storage_result["file_path"],
                filename=storage_result["filename"]
            )
            
            logger.info(f"🎬 File saved to storage:")
            logger.info(f"🎬 - Path: {result.file_path}")
            logger.info(f"🎬 - Size: {result.file_size:,} bytes")
            logger.info(f"🎬 - SHA256: {result.sha256[:16]}...")
            logger.info(f"🎬 - Download URL: {result.download_url}")
            
            return result
            
        except Exception as e:
            logger.error(f"🎬 Storage operation failed for job {job_id}: {e}")
            raise StorageError(
                f"Failed to save clip: {str(e)}",
                job_id=job_id,
                details={"title": title, "data_size": len(video_data)}
            ) 