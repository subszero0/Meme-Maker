import yt_dlp
from fastapi import APIRouter, HTTPException
import logging

from ..models import MetadataRequest, MetadataResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/metadata", response_model=MetadataResponse)
async def get_video_metadata(request: MetadataRequest) -> MetadataResponse:
    """Get video metadata using yt-dlp"""
    try:
        logger.info(f"Fetching metadata for URL: {request.url}")
        
        # Configure yt-dlp to extract metadata only (no download)
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info without downloading
            info = ydl.extract_info(request.url, download=False)
            
            # Handle playlist URLs - take first video
            if 'entries' in info and info['entries']:
                info = info['entries'][0]
            
            # Extract metadata
            title = info.get('title', 'Unknown Video')
            duration = float(info.get('duration', 0))
            thumbnail_url = info.get('thumbnail')
            
            # Get available formats/resolutions
            formats = info.get('formats', [])
            resolutions = []
            for fmt in formats:
                if fmt.get('height'):
                    res = f"{fmt['height']}p"
                    if res not in resolutions:
                        resolutions.append(res)
            
            # Sort resolutions
            resolution_order = ['144p', '240p', '360p', '480p', '720p', '1080p', '1440p', '2160p']
            resolutions.sort(key=lambda x: resolution_order.index(x) if x in resolution_order else 999)
            
            logger.info(f"Successfully extracted metadata: {title}, {duration}s")
            
            return MetadataResponse(
                title=title,
                duration=duration,
                thumbnail_url=thumbnail_url,
                resolutions=resolutions
            )
            
    except Exception as e:
        logger.error(f"Failed to extract metadata from {request.url}: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to extract video metadata: {str(e)}"
        ) 