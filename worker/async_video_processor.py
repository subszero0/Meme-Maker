"""
Async video processor with optimized I/O operations and batch processing.
Implements async patterns for improved performance and concurrency.
"""
import asyncio
import aiofiles
import aiohttp
from typing import List, Dict, Optional, Callable, Any
from datetime import datetime, timedelta
from pathlib import Path
import logging

from .exceptions import VideoProcessingError, DownloadError, ProcessingError
from .progress.tracker import ProgressTracker
from .video.analyzer import VideoAnalyzer
from .video.downloader import VideoDownloader
from .video.trimmer import VideoTrimmer
from .storage.manager import StorageManager


class AsyncVideoProcessor:
    """
    Async video processor with optimized I/O operations.
    Supports batch processing and concurrent job execution.
    """

    def __init__(
        self, max_concurrent_jobs: int = 5, batch_size: int = 10, timeout: int = 300
    ):
        self.max_concurrent_jobs = max_concurrent_jobs
        self.batch_size = batch_size
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.progress_tracker = ProgressTracker()
        self.video_analyzer = VideoAnalyzer()
        self.video_downloader = VideoDownloader()
        self.video_trimmer = VideoTrimmer()
        self.storage_manager = StorageManager()

        # Semaphore for concurrent job control
        self.semaphore = asyncio.Semaphore(max_concurrent_jobs)

        # Job processing statistics
        self.stats = {
            "jobs_processed": 0,
            "jobs_failed": 0,
            "total_processing_time": 0,
            "average_processing_time": 0,
        }

    async def process_video_async(
        self,
        job_id: str,
        url: str,
        start_time: float,
        end_time: float,
        format_id: Optional[str] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Process a single video asynchronously with proper resource management.

        Args:
            job_id: Unique job identifier
            url: Video URL to process
            start_time: Start time in seconds
            end_time: End time in seconds
            format_id: Optional format preference
            progress_callback: Optional progress callback function

        Returns:
            Dictionary with processing results

        Raises:
            VideoProcessingError: If processing fails
        """
        async with self.semaphore:
            start_processing = datetime.now()

            try:
                self.logger.info(f"Starting async processing for job {job_id}")

                # Stage 1: Analyze video metadata (async)
                if progress_callback:
                    progress_callback(5, "Analyzing video")

                metadata = await self._analyze_video_async(url, job_id)

                # Stage 2: Download video (async with progress)
                if progress_callback:
                    progress_callback(15, "Downloading video")

                video_path = await self._download_video_async(
                    url,
                    job_id,
                    format_id,
                    lambda p: progress_callback(15 + int(p * 0.4), "Downloading")
                    if progress_callback
                    else None,
                )

                # Stage 3: Trim video (async)
                if progress_callback:
                    progress_callback(60, "Processing video")

                trimmed_path = await self._trim_video_async(
                    video_path,
                    start_time,
                    end_time,
                    job_id,
                    lambda p: progress_callback(60 + int(p * 0.25), "Trimming")
                    if progress_callback
                    else None,
                )

                # Stage 4: Upload to storage (async)
                if progress_callback:
                    progress_callback(90, "Uploading result")

                download_url = await self._upload_video_async(
                    trimmed_path, job_id, metadata
                )

                # Stage 5: Cleanup temporary files (async)
                await self._cleanup_files_async([video_path, trimmed_path])

                if progress_callback:
                    progress_callback(100, "Complete")

                # Update statistics
                processing_time = (datetime.now() - start_processing).total_seconds()
                await self._update_stats_async(processing_time, success=True)

                result = {
                    "job_id": job_id,
                    "download_url": download_url,
                    "metadata": metadata,
                    "processing_time": processing_time,
                    "status": "completed",
                }

                self.logger.info(
                    f"Completed async processing for job {job_id} in {processing_time:.2f}s"
                )
                return result

            except Exception as e:
                processing_time = (datetime.now() - start_processing).total_seconds()
                await self._update_stats_async(processing_time, success=False)

                self.logger.error(f"Failed async processing for job {job_id}: {str(e)}")
                raise VideoProcessingError(
                    f"Processing failed: {str(e)}", job_id=job_id
                ) from e

    async def process_batch_async(
        self,
        jobs: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[str, int, str], None]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process multiple videos concurrently in batches.

        Args:
            jobs: List of job dictionaries with job_id, url, start_time, end_time
            progress_callback: Optional callback for individual job progress

        Returns:
            List of processing results
        """
        results = []

        # Process jobs in batches to avoid overwhelming the system
        for i in range(0, len(jobs), self.batch_size):
            batch = jobs[i : i + self.batch_size]
            self.logger.info(
                f"Processing batch {i//self.batch_size + 1} with {len(batch)} jobs"
            )

            # Create async tasks for the batch
            tasks = []
            for job in batch:
                task = asyncio.create_task(
                    self.process_video_async(
                        job["job_id"],
                        job["url"],
                        job["start_time"],
                        job["end_time"],
                        job.get("format_id"),
                        lambda p, s, jid=job["job_id"]: progress_callback(jid, p, s)
                        if progress_callback
                        else None,
                    )
                )
                tasks.append(task)

            # Wait for batch completion with timeout
            try:
                batch_results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True), timeout=self.timeout
                )

                # Process results and handle exceptions
                for result in batch_results:
                    if isinstance(result, Exception):
                        self.logger.error(f"Batch job failed: {str(result)}")
                        results.append({"status": "failed", "error": str(result)})
                    else:
                        results.append(result)

            except asyncio.TimeoutError:
                self.logger.error(f"Batch processing timeout after {self.timeout}s")
                # Cancel remaining tasks
                for task in tasks:
                    if not task.done():
                        task.cancel()

                results.extend(
                    [
                        {"status": "timeout", "error": "Processing timeout"}
                        for _ in batch
                    ]
                )

        return results

    async def _analyze_video_async(self, url: str, job_id: str) -> Dict[str, Any]:
        """Async video metadata analysis"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.video_analyzer.analyze_video, url, job_id
        )

    async def _download_video_async(
        self,
        url: str,
        job_id: str,
        format_id: Optional[str],
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> str:
        """Async video download with progress tracking"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.video_downloader.download_video,
            url,
            job_id,
            format_id,
            progress_callback,
        )

    async def _trim_video_async(
        self,
        video_path: str,
        start_time: float,
        end_time: float,
        job_id: str,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> str:
        """Async video trimming"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.video_trimmer.trim_video,
            video_path,
            start_time,
            end_time,
            job_id,
            progress_callback,
        )

    async def _upload_video_async(
        self, video_path: str, job_id: str, metadata: Dict[str, Any]
    ) -> str:
        """Async video upload to storage"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.storage_manager.store_video, video_path, job_id, metadata
        )

    async def _cleanup_files_async(self, file_paths: List[str]) -> None:
        """Async cleanup of temporary files"""
        cleanup_tasks = []

        for file_path in file_paths:
            if file_path and Path(file_path).exists():
                cleanup_tasks.append(self._delete_file_async(file_path))

        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)

    async def _delete_file_async(self, file_path: str) -> None:
        """Async file deletion"""
        try:
            path = Path(file_path)
            if path.exists():
                await asyncio.to_thread(path.unlink)
                self.logger.debug(f"Deleted temporary file: {file_path}")
        except Exception as e:
            self.logger.warning(f"Failed to delete file {file_path}: {str(e)}")

    async def _update_stats_async(self, processing_time: float, success: bool) -> None:
        """Update processing statistics asynchronously"""
        if success:
            self.stats["jobs_processed"] += 1
        else:
            self.stats["jobs_failed"] += 1

        self.stats["total_processing_time"] += processing_time
        total_jobs = self.stats["jobs_processed"] + self.stats["jobs_failed"]

        if total_jobs > 0:
            self.stats["average_processing_time"] = (
                self.stats["total_processing_time"] / total_jobs
            )

    async def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        return self.stats.copy()

    async def health_check(self) -> Dict[str, Any]:
        """Async health check for the processor"""
        return {
            "status": "healthy",
            "concurrent_jobs_limit": self.max_concurrent_jobs,
            "batch_size": self.batch_size,
            "timeout": self.timeout,
            "stats": await self.get_processing_stats(),
        }


# Utility functions for async operations
async def process_video_with_timeout(
    processor: AsyncVideoProcessor, job_data: Dict[str, Any], timeout: int = 300
) -> Dict[str, Any]:
    """Process video with timeout handling"""
    try:
        return await asyncio.wait_for(
            processor.process_video_async(**job_data), timeout=timeout
        )
    except asyncio.TimeoutError:
        raise VideoProcessingError(f"Processing timeout after {timeout}s")


async def create_async_processor_pool(
    pool_size: int = 3, max_concurrent_per_processor: int = 5
) -> List[AsyncVideoProcessor]:
    """Create a pool of async video processors for load balancing"""
    processors = []

    for i in range(pool_size):
        processor = AsyncVideoProcessor(
            max_concurrent_jobs=max_concurrent_per_processor
        )
        processors.append(processor)

    return processors
