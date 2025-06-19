import yt_dlp
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
import logging
import asyncio
import time
from typing import List, Dict, Optional

from ..models import MetadataRequest, MetadataResponse

router = APIRouter()
logger = logging.getLogger(__name__)

class UrlRequest(BaseModel):
    url: HttpUrl

class VideoFormat(BaseModel):
    format_id: str
    ext: str
    resolution: str
    filesize: Optional[int] = None
    fps: Optional[float] = None
    vcodec: str
    acodec: str
    format_note: str

class VideoMetadata(BaseModel):
    title: str
    duration: float
    thumbnail: str
    uploader: str
    upload_date: str
    view_count: int
    formats: List[VideoFormat]

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

@router.post("/metadata/extract", response_model=VideoMetadata)
async def extract_video_metadata(request: UrlRequest):
    """Extract video metadata including available formats/resolutions"""
    try:
        url = str(request.url)
        logger.info(f"🔍 Extracting metadata for: {url}")
        
        # Configure yt-dlp for metadata extraction with robust format detection
        # Match worker configuration for consistency
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android_creator', 'web'],
                    'skip': ['dash']
                }
            },
            'http_headers': {
                'User-Agent': 'com.google.android.apps.youtube.creator/24.47.100 (Linux; U; Android 14; SM-S918B) gzip',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract metadata without downloading
            try:
                info = await asyncio.to_thread(ydl.extract_info, url, download=False)
            except Exception as extract_error:
                logger.error(f"❌ yt-dlp extraction failed: {extract_error}")
                # Try with different configuration if first attempt fails
                ydl_opts_fallback = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['tv', 'web'],
                        }
                    }
                }
                with yt_dlp.YoutubeDL(ydl_opts_fallback) as ydl_fallback:
                    info = await asyncio.to_thread(ydl_fallback.extract_info, url, download=False)
            
            # Handle playlists by taking first video
            if 'entries' in info and info['entries']:
                info = info['entries'][0]
            
            # Extract basic metadata
            title = info.get('title', 'Unknown')
            duration = float(info.get('duration', 0))
            thumbnail = info.get('thumbnail', '')
            uploader = info.get('uploader', 'Unknown')
            upload_date = info.get('upload_date', '')
            view_count = int(info.get('view_count', 0))
            
            # Extract and filter video formats with enhanced logging
            formats = []
            seen_format_ids = set()
            
            logger.info(f"🔍 Backend: Processing {len(info.get('formats', []))} total formats from yt-dlp")
            
            for fmt in info.get('formats', []):
                # Only include formats that have video streams (exclude audio-only)
                if (fmt.get('vcodec') != 'none' and 
                    fmt.get('height') and 
                    fmt.get('width') and
                    fmt.get('format_id') not in seen_format_ids):
                    
                    resolution = f"{fmt.get('width')}x{fmt.get('height')}"
                    format_id = fmt.get('format_id', '')
                    
                    # Avoid duplicate format IDs but allow multiple formats per resolution
                    seen_format_ids.add(format_id)
                    
                    format_obj = VideoFormat(
                        format_id=format_id,
                        ext=fmt.get('ext', 'mp4'),
                        resolution=resolution,
                        filesize=fmt.get('filesize'),
                        fps=fmt.get('fps'),
                        vcodec=fmt.get('vcodec', 'unknown'),
                        acodec=fmt.get('acodec', 'unknown'),
                        format_note=fmt.get('format_note', '')
                    )
                    formats.append(format_obj)
                    
                    # Log first few formats for debugging
                    if len(formats) <= 5:
                        logger.info(f"🔍 Backend: Format {format_id}: {resolution} ({fmt.get('vcodec')}/{fmt.get('acodec')})")
            
            # Sort formats by resolution (descending), then by filesize (descending)
            def resolution_sort_key(fmt):
                try:
                    width, height = map(int, fmt.resolution.split('x'))
                    filesize = fmt.filesize or 0
                    return (width * height, filesize)
                except:
                    return (0, 0)
            
            formats.sort(key=resolution_sort_key, reverse=True)
            
            # Increase limit to show more available formats
            formats = formats[:20]
            
            metadata = VideoMetadata(
                title=title,
                duration=duration,
                thumbnail=thumbnail,
                uploader=uploader,
                upload_date=upload_date,
                view_count=view_count,
                formats=formats
            )
            
            logger.info(f"✅ Extracted metadata: {title} - {len(formats)} formats")
            logger.info(f"🔍 Backend: Format IDs extracted: {[f.format_id for f in formats[:10]]}")  # Log first 10 format IDs
            return metadata
            
    except Exception as e:
        logger.error(f"❌ Failed to extract metadata: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to extract video metadata: {str(e)}"
        ) 