# Import Redis and Job model to get video title
import sys
import urllib.parse
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

# Module path setup (must be after standard imports)
sys.path.append("/app/backend")
from app import redis

router = APIRouter()

CLIPS_DIR = Path("/app/clips")


@router.get("/clips/{filename}")
async def download_clip(filename: str):
    """Download a processed video clip"""
    # Extract job_id from filename (could be video_title.mp4 or video_title_job_id.mp4)
    if not filename.endswith(".mp4"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file format"
        )

    # Security: validate filename to prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename"
        )

    clip_path = CLIPS_DIR / filename

    if not clip_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found or expired"
        )

    # Try to get video title from Redis by finding job that produced this file
    video_title = None
    try:
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


@router.delete("/clips/{job_id}.mp4")
async def cleanup_clip(job_id: str):
    """Clean up a processed clip (called after successful download)"""
    # Validate job_id to prevent path traversal
    if not job_id.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job ID format"
        )

    clip_path = CLIPS_DIR / f"{job_id}.mp4"

    if clip_path.exists():
        try:
            clip_path.unlink()
            return {"message": "Clip deleted successfully"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete clip: {str(e)}",
            )

    return {"message": "Clip not found (already cleaned up)"}
