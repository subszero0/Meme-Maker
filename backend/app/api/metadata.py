from fastapi import APIRouter

from ..models import MetadataRequest, MetadataResponse

router = APIRouter()


@router.post("/metadata", response_model=MetadataResponse)
async def get_video_metadata(request: MetadataRequest) -> MetadataResponse:
    """Get video metadata - temporarily returning working placeholder while we debug connection"""
    # Temporarily return working response to fix connection first
    return MetadataResponse(
        title="Sample Video",
        duration=1207.0,  # 20 minutes 07 seconds as user mentioned
        thumbnail_url="https://example.com/thumb.jpg",
        resolutions=["720p", "1080p"]
    ) 