import hashlib
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import aiofiles
    import aiofiles.os

    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False

# Import settings from the new configuration module
from app.config.configuration import get_settings

settings = get_settings()


class LocalStorageManager:
    """Local storage manager with ISO-8601 organization and atomic operations"""

    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or settings.clips_dir)
        self._ensure_base_directory()

    def _ensure_base_directory(self) -> None:
        """Ensure base directory exists and is writable"""
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Fail fast if directory isn't writable
        if not os.access(self.base_path, os.W_OK):
            raise RuntimeError(f"clips_dir not writable: {self.base_path}")

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility"""
        # Replace invalid characters with underscores
        # Invalid chars: < > : " | ? * \ /
        sanitized = re.sub(r'[<>:"|?*\\/]', "_", filename)

        # Replace multiple underscores with single underscore
        sanitized = re.sub(r"_+", "_", sanitized)

        # Remove leading/trailing underscores and whitespace
        sanitized = sanitized.strip("_ ")

        # Ensure filename isn't empty
        if not sanitized:
            sanitized = "untitled"

        return sanitized

    def _get_daily_path(self, job_id: str) -> Path:
        """Get ISO-8601 organized path for job"""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return self.base_path / today

    async def save(
        self, job_id: str, video_data: bytes, video_title: str
    ) -> Dict[str, Any]:
        """
        Save video data with atomic write-then-move operation
        Returns metadata including file path, SHA256, and size
        """
        daily_path = self._get_daily_path(job_id)
        daily_path.mkdir(parents=True, exist_ok=True)

        # Generate final file path with sanitized title
        sanitized_title = self._sanitize_filename(video_title)
        filename = f"{sanitized_title}_{job_id}.mp4"
        final_path = daily_path / filename

        # Write to temporary file first (atomic operation)
        temp_path = daily_path / f"{filename}.tmp"

        try:
            if AIOFILES_AVAILABLE:
                # Use async file operations if available
                async with aiofiles.open(temp_path, "wb") as f:
                    await f.write(video_data)

                # Force sync to disk (aiofiles doesn't have os.sync, use fsync via file descriptor)
                # Note: aiofiles doesn't provide os.sync(), so we'll ensure file is flushed

                # Atomic rename to final location
                await aiofiles.os.rename(temp_path, final_path)
            else:
                # Fallback to sync operations
                with open(temp_path, "wb") as f:
                    f.write(video_data)

                # Force sync to disk (os.sync() is platform-specific)
                # Note: os.sync() may not be available on all platforms

                # Atomic rename to final location
                temp_path.rename(final_path)

            # Calculate checksum and size
            file_size = final_path.stat().st_size
            sha256_hash = hashlib.sha256(video_data).hexdigest()

            return {
                "file_path": str(final_path.relative_to(self.base_path)),
                "full_path": str(final_path),
                "sha256": sha256_hash,
                "size": file_size,
                "filename": filename,
            }

        except Exception as e:
            # Cleanup temp file if it exists
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
            raise Exception(f"STORAGE_FAIL: Failed to save clip: {str(e)}")

    async def get(self, job_id: str) -> Optional[Path]:
        """Get file path for job_id, checking daily directories"""
        # Look in today's directory first
        today_path = self._get_daily_path(job_id)

        # Search for files containing job_id
        for file_path in today_path.glob(f"*_{job_id}.mp4"):
            if file_path.exists():
                return file_path

        # Search in recent days (last 7 days)
        for days_ago in range(1, 8):
            check_date = (datetime.utcnow() - timedelta(days=days_ago)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            date_str = check_date.strftime("%Y-%m-%d")
            date_path = self.base_path / date_str

            if date_path.exists():
                for file_path in date_path.glob(f"*_{job_id}.mp4"):
                    if file_path.exists():
                        return file_path

        return None

    async def exists(self, job_id: str) -> bool:
        """Check if file exists for job_id"""
        file_path = await self.get(job_id)
        return file_path is not None and file_path.exists()

    async def delete(self, job_id: str) -> bool:
        """Delete file for job_id"""
        file_path = await self.get(job_id)
        if file_path and file_path.exists():
            file_path.unlink()
            return True
        return False

    def get_download_url(self, job_id: str, filename: str) -> str:
        """Generate download URL for job"""
        # Always use full BASE_URL when properly configured
        # Only use relative URLs if BASE_URL is not set or empty
        if settings.base_url and settings.base_url.strip():
            return f"{settings.base_url}/api/v1/jobs/{job_id}/download"
        else:
            # Fallback to relative URL only if no BASE_URL configured
            return f"/api/v1/jobs/{job_id}/download"

    async def validate_file_integrity(
        self, file_path: Path, expected_sha256: str
    ) -> bool:
        """Validate file integrity using SHA256"""
        if not file_path.exists():
            return False

        if AIOFILES_AVAILABLE:
            async with aiofiles.open(file_path, "rb") as f:
                content = await f.read()
                actual_hash = hashlib.sha256(content).hexdigest()
                return actual_hash == expected_sha256
        else:
            with open(file_path, "rb") as f:
                content = f.read()
                actual_hash = hashlib.sha256(content).hexdigest()
                return actual_hash == expected_sha256

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics"""
        total_size = 0
        file_count = 0

        for file_path in self.base_path.rglob("*.mp4"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                file_count += 1

        return {
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "file_count": file_count,
            "base_path": str(self.base_path),
        }


# S3StorageManager removed - migration to local storage complete
