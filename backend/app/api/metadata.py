from fastapi import APIRouter

from ..models import MetadataRequest, MetadataResponse

router = APIRouter()


@router.post("/metadata", response_model=MetadataResponse)
async def get_video_metadata(request: MetadataRequest) -> MetadataResponse:
    """Get video metadata including duration and title"""
    # Placeholder implementation
    return MetadataResponse(
        title="Sample Video Title",
        duration=123.45,  # seconds
        thumbnail_url="https://example.com/thumbnail.jpg",
        resolutions=["720p", "1080p"]
    ) 