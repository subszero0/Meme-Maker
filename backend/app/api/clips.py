# Import Redis and Job model to get video title
import os
import re
import sys
import urllib.parse
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

# Module path setup (must be after standard imports)
sys.path.append("/app/backend")
from app import redis  # noqa: E402
from app.dependencies import get_storage  # noqa: E402
from app.storage import LocalStorageManager  # noqa: E402

router = APIRouter()

CLIPS_DIR = Path("/app/clips")


def validate_filename_security(filename: str) -> bool:
    """
    Comprehensive filename validation to prevent directory traversal and other attacks
    """
    # Basic checks
    if not filename:
        return False
    
    # Must end with .mp4
    if not filename.endswith(".mp4"):
        return False
    
    # Check for directory traversal patterns
    dangerous_patterns = [
        "..", "/", "\\", ":", "*", "?", '"', "<", ">", "|",
        "\x00", "\n", "\r", "\t"  # Null bytes and control characters
    ]
    
    for pattern in dangerous_patterns:
        if pattern in filename:
            return False
    
    # Only allow alphanumeric, hyphens, underscores, spaces, and dots (but not ..)
    if not re.match(r'^[a-zA-Z0-9\-_\s\.]+\.mp4$', filename):
        return False
    
    # Prevent hidden files
    if filename.startswith('.'):
        return False
    
    # Length check (reasonable filename length)
    if len(filename) > 255:
        return False
    
    # Ensure the filename doesn't resolve to a path outside clips directory
    try:
        clip_path = CLIPS_DIR / filename
        resolved_path = clip_path.resolve()
        clips_dir_resolved = CLIPS_DIR.resolve()
        
        # Check if the resolved path is within the clips directory
        if not str(resolved_path).startswith(str(clips_dir_resolved)):
            return False
    except (OSError, ValueError):
        return False
    
    return True


@router.get("/clips/{filename}")
async def download_clip(filename: str):
    """Download a processed video clip"""
    
    # Comprehensive security validation
    if not validate_filename_security(filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid filename: filename failed security validation"
        )

    clip_path = CLIPS_DIR / filename

    # Additional check: ensure file exists and is actually a file
    if not clip_path.exists() or not clip_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found or expired"
        )

    # Try to get video title from Redis by finding job that produced this file
    video_title = None
    try:
        if redis is not None:
            # Scan for jobs to find the one with matching download_url
            cursor = 0
            while True:
                cursor, keys = redis.scan(cursor, match="job:*", count=100)
                for key in keys:
                    job_data = redis.hgetall(key)
                    if job_data and job_data.get(b"download_url"):
                        download_url = job_data.get(b"download_url").decode()
                        if filename in download_url:
                            video_title = job_data.get(b"video_title")
                            if video_title:
                                video_title = video_title.decode()
                            break
                if cursor == 0 or video_title:
                    break
    except Exception as e:
        print(f"Warning: Could not get video title from Redis: {e}")

    # Use video title as download filename, fallback to original filename
    download_filename = f"{video_title}.mp4" if video_title else filename

    # Ensure filename is safe for HTTP headers
    safe_filename = urllib.parse.quote(download_filename.encode("utf-8"))

    # Get file size for content-length header
    file_size = clip_path.stat().st_size

    # Return file with proper video title as download name
    return FileResponse(
        path=str(clip_path),
        media_type="video/mp4",
        filename=download_filename,
        headers={
            "Content-Disposition": (
                f'attachment; filename="{download_filename}"; '
                f"filename*=UTF-8''{safe_filename}"
            ),
            "Content-Length": str(file_size),
        },
    )


@router.delete("/clips/{job_id}")
async def cleanup_clip(
    job_id: str, storage: LocalStorageManager = Depends(get_storage)
):
    """Clean up a processed clip (called after successful download)"""
    # Validate job_id to prevent path traversal
    if not job_id.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job ID format"
        )

    try:
        # Use storage manager to delete the file (handles dated directory structure)
        deleted = await storage.delete(job_id)

        if deleted:
            return {"message": "Clip deleted successfully"}
        else:
            return {"message": "Clip not found (already cleaned up)"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete clip: {str(e)}",
        )
