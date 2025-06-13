from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
import os

router = APIRouter()

CLIPS_DIR = Path("/app/clips")

@router.get("/clips/{job_id}.mp4")
async def download_clip(job_id: str):
    """Download a processed video clip"""
    # Validate job_id to prevent path traversal
    if not job_id.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job ID format"
        )
    
    clip_path = CLIPS_DIR / f"{job_id}.mp4"
    
    if not clip_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clip not found or expired"
        )
    
    # Get file size for content-length header
    file_size = clip_path.stat().st_size
    
    # Return file with appropriate headers
    return FileResponse(
        path=str(clip_path),
        media_type="video/mp4",
        filename=f"clip_{job_id}.mp4",
        headers={
            "Content-Disposition": "attachment; filename=clip.mp4",
            "Content-Length": str(file_size)
        }
    )

@router.delete("/clips/{job_id}.mp4")
async def cleanup_clip(job_id: str):
    """Clean up a processed clip (called after successful download)"""
    # Validate job_id to prevent path traversal
    if not job_id.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job ID format"
        )
    
    clip_path = CLIPS_DIR / f"{job_id}.mp4"
    
    if clip_path.exists():
        try:
            clip_path.unlink()
            return {"message": "Clip deleted successfully"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete clip: {str(e)}"
            )
    
    return {"message": "Clip not found (already cleaned up)"} 