"""
Video Processing Orchestrator

Main orchestrator that coordinates video download, trimming, and storage operations
with clear error boundaries and proper exception handling.
"""

import logging
import tempfile
import shutil
import time
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

# Try relative imports with fallback for testing
try:
    from .downloader import VideoDownloader
    from .trimmer import VideoTrimmer
    from .analyzer import VideoAnalyzer
    from ..storage.manager import StorageManager, StorageResult
    from ..progress.tracker import ProgressTracker
    from ..exceptions import (
        VideoProcessingError, DownloadError, TrimError, StorageError,
        ValidationError, VideoAnalysisError
    )
except ImportError:
    # For testing, create mock classes and imports
    class VideoDownloader:
        def __init__(self, *args): pass
        async def download(self, *args): return Path("/tmp/video.mp4")
    class VideoTrimmer:
        def __init__(self, *args): pass
        async def trim(self, *args): return Path("/tmp/trimmed.mp4")
    class VideoAnalyzer:
        def __init__(self, *args): pass
        def extract_video_title(self, *args): return "test_video"
        async def analyze_video_file(self, *args): return {}
    class StorageManager:
        def __init__(self, *args): pass
        async def save(self, *args): return None
    class StorageResult:
        pass
    class ProgressTracker:
        def __init__(self, *args): 
            self.job_id = "test_job"
        def update(self, *args): pass
        def update_error(self, *args): pass
    
    # Mock exceptions
    class VideoProcessingError(Exception): pass
    class DownloadError(Exception): 
        error_code = "DOWNLOAD_ERROR"
    class TrimError(Exception): 
        error_code = "TRIM_ERROR"
    class StorageError(Exception): 
        error_code = "STORAGE_ERROR"
    class ValidationError(Exception): 
        def __init__(self, message, job_id=None):
            super().__init__(message)
            self.job_id = job_id
            self.error_code = "VALIDATION_ERROR"
    class VideoAnalysisError(Exception): 
        error_code = "ANALYSIS_ERROR"

# Try to import from backend app, but handle gracefully for testing
try:
    import sys
    sys.path.append('/app/backend')
    from app import redis
    from app.models import JobStatus
except ImportError:
    # For testing, create mock objects
    redis = None
    class JobStatus:
        class working:
            value = "working"
        class done:
            value = "done"
        class error:
            value = "error"

logger = logging.getLogger(__name__)


@dataclass
class ProcessingRequest:
    """Request data for video processing"""
    job_id: str
    url: str
    in_ts: float
    out_ts: float
    format_id: Optional[str] = None


@dataclass
class ProcessingResult:
    """Result of video processing operation"""
    success: bool
    storage_result: Optional[StorageResult] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    video_title: Optional[str] = None


class VideoProcessor:
    """Main processing orchestrator with clear error boundaries"""
    
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.progress_tracker = ProgressTracker(job_id)
        self.downloader = VideoDownloader(self.progress_tracker)
        self.trimmer = VideoTrimmer(self.progress_tracker)
        self.analyzer = VideoAnalyzer(self.progress_tracker)
        self.storage = StorageManager(self.progress_tracker)
        self.temp_dir: Optional[Path] = None
    
    async def process(self, request: ProcessingRequest) -> ProcessingResult:
        """
        Main processing orchestrator with clear error boundaries
        
        Args:
            request: Processing request with all necessary parameters
            
        Returns:
            ProcessingResult with success status and results or error details
        """
        start_time = time.monotonic()
        
        try:
            logger.info(f"🎬 Starting job {request.job_id}: {request.url} [{request.in_ts}s - {request.out_ts}s] format: {request.format_id}")
            
            # Validate request
            self._validate_request(request)
            
            # Create temporary directory
            self.temp_dir = Path(tempfile.mkdtemp(prefix=f"clip_{request.job_id}_"))
            
            # Step 1: Extract video title
            video_title = self.analyzer.extract_video_title(request.url)
            logger.info(f"🎬 Using video title: '{video_title}'")
            
            # Step 2: Download video
            self.progress_tracker.update(5, JobStatus.working.value, "Initializing download...")
            video_file = await self.downloader.download(
                request.url, 
                request.format_id, 
                self.temp_dir
            )
            
            # Step 3: Analyze downloaded video
            analysis_result = await self.analyzer.analyze_video_file(video_file)
            
            # Step 4: Trim video
            processed_file = await self.trimmer.trim(video_file, request.in_ts, request.out_ts)
            
            # Step 5: Store processed video
            with open(processed_file, 'rb') as f:
                video_data = f.read()
            
            storage_result = await self.storage.save(request.job_id, video_data, video_title)
            
            # Step 6: Mark job as complete
            await self._mark_job_complete(request.job_id, storage_result, video_title)
            
            processing_time = time.monotonic() - start_time
            logger.info(f"✅ Job {request.job_id} completed successfully in {processing_time:.2f}s")
            
            return ProcessingResult(
                success=True,
                storage_result=storage_result,
                processing_time=processing_time,
                video_title=video_title
            )
            
        except (DownloadError, TrimError, StorageError, VideoAnalysisError, ValidationError) as e:
            logger.error(f"Processing failed for job {request.job_id}: {e}")
            self.progress_tracker.update_error(e.error_code, str(e))
            
            processing_time = time.monotonic() - start_time
            return ProcessingResult(
                success=False,
                error_code=e.error_code,
                error_message=str(e),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Unexpected error in job {request.job_id}: {e}")
            self.progress_tracker.update_error('UNKNOWN_ERROR', str(e))
            
            processing_time = time.monotonic() - start_time
            return ProcessingResult(
                success=False,
                error_code='UNKNOWN_ERROR',
                error_message=str(e),
                processing_time=processing_time
            )
            
        finally:
            # Cleanup
            await self._cleanup()
    
    def _validate_request(self, request: ProcessingRequest) -> None:
        """
        Validate processing request parameters
        
        Args:
            request: Processing request to validate
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate timestamps
        if request.in_ts < 0:
            logger.warning(f"⚠️ Negative start timestamp: {request.in_ts}s")
        
        if request.out_ts <= request.in_ts:
            raise ValidationError(
                f"Invalid timestamps: end ({request.out_ts}s) must be greater than start ({request.in_ts}s)",
                job_id=request.job_id
            )
        
        clip_duration = request.out_ts - request.in_ts
        if clip_duration < 0.1:
            logger.warning(f"⚠️ Very short clip duration: {clip_duration:.3f}s")
        
        if clip_duration > 180:  # 3 minutes
            raise ValidationError(
                f"Clip duration ({clip_duration:.1f}s) exceeds maximum allowed (180s)",
                job_id=request.job_id
            )
        
        # Validate format_id
        if request.format_id == "None":
            logger.warning("🎬 format_id is string 'None' - check serialization!")
        elif request.format_id is None:
            logger.warning("🎬 format_id is None - resolution picker not working!")
        else:
            logger.info(f"🎬 Using user-selected format: {request.format_id}")
        
        # Log timing details
        logger.info(f"🎬 TIMING ANALYSIS:")
        logger.info(f"🎬 - Start timestamp: {request.in_ts}s")
        logger.info(f"🎬 - End timestamp: {request.out_ts}s") 
        logger.info(f"🎬 - Expected duration: {clip_duration:.3f}s")
    
    async def _mark_job_complete(self, job_id: str, storage_result: StorageResult, video_title: str) -> None:
        """
        Mark job as complete in Redis with metadata
        
        Args:
            job_id: Job identifier
            storage_result: Storage operation result
            video_title: Video title
        """
        try:
            self.progress_tracker.update(98, stage="Finalizing...")
            
            job_key = f"job:{job_id}"
            completion_data = {
                "status": str(JobStatus.done.value),
                "progress": "100",
                "download_url": str(storage_result.download_url),
                "video_title": str(video_title),
                "file_size": str(storage_result.file_size),
                "file_sha256": str(storage_result.sha256),
                "completed_at": str(datetime.utcnow().isoformat())
            }
            
            redis.hset(job_key, mapping=completion_data)
            redis.expire(job_key, 3600)
            
            self.progress_tracker.update(100, JobStatus.done.value, "Complete! Ready for download")
            logger.info(f"✅ Job {job_id} marked as completed with download URL")
            
        except Exception as e:
            logger.error(f"Failed to mark job {job_id} as complete: {e}")
            # Don't raise here as the processing was successful
    
    async def _cleanup(self) -> None:
        """Clean up temporary files and resources"""
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temp directory: {self.temp_dir}")
            except Exception as e:
                logger.error(f"Failed to cleanup temp dir {self.temp_dir}: {e}") 