from fastapi import APIRouter, Depends, HTTPException

from ..models import MetadataRequest, MetadataResponse
from ..ratelimit import global_limiter

router = APIRouter()


@router.post(
    "/metadata", response_model=MetadataResponse, dependencies=[Depends(global_limiter)]
)
async def get_video_metadata(request: MetadataRequest) -> MetadataResponse:
    """Get video metadata including duration and title

    Rate limits:
    - Global: 10 requests per minute per IP
    """
    # Basic URL validation for supported platforms
    url_str = str(request.url).lower()
    supported_domains = [
        "youtube.com", "youtu.be", "instagram.com", 
        "facebook.com", "reddit.com", "threads.net"
    ]
    
    # Check if URL contains any supported domain
    if not any(domain in url_str for domain in supported_domains):
        raise HTTPException(
            status_code=400, 
            detail="Please provide a valid video URL from YouTube, Instagram, Facebook, Threads, or Reddit."
        )
    
    # Placeholder implementation for valid URLs
    return MetadataResponse(
        url=str(request.url),
        title="Sample Video Title",
        duration=123.45,  # seconds
        thumbnail_url="https://example.com/thumbnail.jpg",
        resolutions=["720p", "1080p"],
    )
