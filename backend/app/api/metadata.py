from fastapi import APIRouter, Depends

from ..models import MetadataRequest, MetadataResponse
from ..ratelimit import global_limiter

router = APIRouter()


@router.post("/metadata", response_model=MetadataResponse, dependencies=[Depends(global_limiter)])
async def get_video_metadata(request: MetadataRequest) -> MetadataResponse:
    """Get video metadata including duration and title
    
    Rate limits:
    - Global: 10 requests per minute per IP
    """
    # Placeholder implementation
    return MetadataResponse(
        title="Sample Video Title",
        duration=123.45,  # seconds
        thumbnail_url="https://example.com/thumbnail.jpg",
        resolutions=["720p", "1080p"]
    ) 