import asyncio
import logging
import time
from typing import Dict, List, Optional

import yt_dlp
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from yt_dlp.utils import DownloadError

from ..cache.metadata_cache import MetadataCache
from ..dependencies import get_async_redis
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


def get_optimized_ydl_opts() -> Dict:
    """Get optimized yt-dlp configuration for fast metadata extraction with bot detection avoidance"""
    return {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,  # Only extract metadata, don't download
        "extractor_args": {
            "youtube": {
                "player_client": ["ios", "android_creator", "web"],
                "skip": ["dash"],  # Skip DASH for faster extraction
                "max_comments": ["0"],  # Don't fetch comments
                "comment_sort": ["top"],
            }
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
        },
        "socket_timeout": 30,
        "retries": 3,
    }


def get_fallback_ydl_opts() -> List[Dict]:
    """Get fallback configurations if primary fails - multiple strategies for bot detection avoidance"""
    return [
        # TV client fallback (often bypasses restrictions)
        {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "skip_download": True,
            "extractor_args": {
                "youtube": {"player_client": ["tv_embedded"], "skip": ["dash", "hls"]}
            },
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (SMART-TV; LINUX; Tizen 2.4.0) AppleWebKit/538.1 (KHTML, like Gecko) Version/2.4.0 TV Safari/538.1"
            },
            "socket_timeout": 30,
        },
        # Android fallback with different user agent
        {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "skip_download": True,
            "extractor_args": {
                "youtube": {"player_client": ["android"], "skip": ["dash"]}
            },
            "http_headers": {
                "User-Agent": "com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip"
            },
            "socket_timeout": 30,
        },
        # Web client with desktop user agent
        {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "skip_download": True,
            "extractor_args": {
                "youtube": {
                    "player_client": ["web"],
                }
            },
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
            "socket_timeout": 30,
        },
        # Simple fallback without extra configurations
        {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "skip_download": True,
            "socket_timeout": 30,
        },
    ]


async def extract_metadata_with_fallback(url: str) -> Dict:
    """Extract metadata with fallback configurations and smart retry for bot detection"""
    configs = [get_optimized_ydl_opts()] + get_fallback_ydl_opts()
    
    # Smart retry parameters for bot detection - REDUCED for better UX
    max_retries = 2  # Reduced from 3 to 2 
    base_wait_time = 30  # Reduced from 120s to 30s (start with 30s, then 60s)
    
    for retry_attempt in range(max_retries):
        for i, ydl_opts in enumerate(configs):
            try:
                logger.info(
                    f"🔍 Attempting metadata extraction with config {i+1}/{len(configs)} (retry {retry_attempt + 1}/{max_retries})"
                )

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    if info:
                        logger.info(f"✅ Successfully extracted metadata with config {i+1} (retry {retry_attempt + 1})")
                        return info
                    
            except DownloadError as e:
                error_str = str(e).lower()
                
                # Check for bot detection/rate limiting patterns
                if (
                    "sign in" in error_str
                    or "confirm you're not a bot" in error_str
                    or "too many requests" in error_str
                    or "http error 429" in error_str
                ):
                    logger.warning(f"⚠️ YouTube bot detection triggered (config {i+1}, retry {retry_attempt + 1}): {e}")
                    
                    # If this is the last config and not the last retry, wait before retrying
                    if i == len(configs) - 1 and retry_attempt < max_retries - 1:
                        wait_time = base_wait_time * (2 ** retry_attempt)  # 30s, then 60s
                        logger.info(f"🕒 YouTube rate limit detected. Waiting {wait_time}s before retry {retry_attempt + 2}/{max_retries}...")
                        logger.info(f"💡 This is normal for YouTube videos - we're working around temporary restrictions")
                        await asyncio.sleep(wait_time)
                        break  # Break inner loop to start next retry attempt
                    
                    # If this is the last retry, raise the exception
                    if retry_attempt == max_retries - 1:
                        logger.error(f"❌ Final retry failed after {max_retries} attempts")
                        raise
                    
                    # Continue to next config
                    continue
                    
                else:
                    # Other DownloadError - continue to next config
                    logger.warning(f"⚠️ DownloadError with config {i+1}: {e}")
                    continue
                    
            except Exception as e:
                logger.warning(f"⚠️ Unexpected error with config {i+1}: {e}")
                continue
    
    # If we get here, all configs and retries failed
    raise DownloadError("Failed to extract metadata after all retry attempts")


@router.post("/metadata", response_model=MetadataResponse)
async def get_video_metadata(
    request: MetadataRequest, redis_client=Depends(get_async_redis)
) -> MetadataResponse:
    """Get video metadata using yt-dlp with caching"""
    url = str(request.url)
    logger.info(f"📋 Fetching metadata for URL: {url}")

    # Initialize cache
    cache = MetadataCache(redis_client)

    # Check cache first with performance logging
    cache_start_time = time.time()
    cached_metadata = await cache.get_metadata(url)
    cache_time = time.time() - cache_start_time

    if cached_metadata:
        logger.info(
            f"✅ Cache hit for metadata: {url} (cache lookup: {cache_time:.3f}s)"
        )
        metadata = cached_metadata.get("metadata", {})
        return MetadataResponse(
            title=metadata.get("title", "Unknown Video"),
            duration=metadata.get("duration", 0),
            thumbnail_url=metadata.get("thumbnail_url"),
            resolutions=metadata.get("resolutions", []),
        )
    else:
        logger.info(
            f"❌ Cache miss for metadata: {url} (cache lookup: {cache_time:.3f}s)"
        )

    # Anti-bot detection: Add small delay for non-cached requests
    await asyncio.sleep(2)  # 2-second delay to appear more human-like

    try:
        # Extract metadata
        start_time = time.time()
        info = await extract_metadata_with_fallback(url)
        extraction_time = time.time() - start_time

        # Extract basic metadata
        title = info.get("title", "Unknown Video")
        duration = float(info.get("duration", 0))
        thumbnail_url = info.get("thumbnail")

        # Get available formats/resolutions
        formats = info.get("formats", [])
        resolutions = []
        for fmt in formats:
            if fmt.get("height"):
                res = f"{fmt['height']}p"
                if res not in resolutions:
                    resolutions.append(res)

        # Sort resolutions
        resolution_order = [
            "144p",
            "240p",
            "360p",
            "480p",
            "720p",
            "1080p",
            "1440p",
            "2160p",
        ]
        resolutions.sort(
            key=lambda x: resolution_order.index(x) if x in resolution_order else 999
        )

        # Cache the result
        metadata_to_cache = {
            "title": title,
            "duration": duration,
            "thumbnail_url": thumbnail_url,
            "resolutions": resolutions,
            "extraction_time": extraction_time,
        }

        await cache.set_metadata(url, metadata_to_cache)

        logger.info(
            f"✅ Successfully extracted metadata: {title}, {duration}s in {extraction_time:.2f}s"
        )

        return MetadataResponse(
            title=title,
            duration=duration,
            thumbnail_url=thumbnail_url,
            resolutions=resolutions,
        )
    except DownloadError as e:
        error_str = str(e).lower()
        # More comprehensive check for bot detection/rate limiting
        if (
            "http error 429" in error_str
            or "too many requests" in error_str
            or "sign in" in error_str
            or "confirm you're not a bot" in error_str
        ):
            logger.warning(f"YouTube bot detection or rate limiting for {url}: {e}")
            raise HTTPException(
                status_code=429,
                detail="YouTube is temporarily blocking automated requests. Please try again later or use a different video.",
            )
        logger.error(f"❌ Failed to extract metadata for {url}: {e}")
        # Return 503 as service is unavailable from our end
        raise HTTPException(
            status_code=503,
            detail="The video service is currently unavailable. Please try again later.",
        )
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred for {url}: {e}")
        raise HTTPException(
            status_code=500, detail="An unexpected server error occurred."
        )


@router.post("/metadata/extract", response_model=VideoMetadata)
async def extract_video_metadata(
    request: UrlRequest, redis_client=Depends(get_async_redis)
):
    """Extract video metadata including available formats/resolutions with caching"""
    try:
        url = str(request.url)
        logger.info(f"🔍 Extracting detailed metadata for: {url}")

        # Initialize cache
        cache = MetadataCache(redis_client)

        # Check cache first (use proper cache key generation for detailed metadata)
        cached_detailed = await cache.get_format_metadata(url)
        if cached_detailed:
            logger.info(f"✅ Cache hit for detailed metadata: {url}")
            metadata = cached_detailed.get("metadata", {})

            # Reconstruct VideoFormat objects
            formats = []
            for fmt_data in metadata.get("formats", []):
                formats.append(VideoFormat(**fmt_data))

            return VideoMetadata(
                title=metadata.get("title", "Unknown"),
                duration=metadata.get("duration", 0),
                thumbnail=metadata.get("thumbnail", ""),
                uploader=metadata.get("uploader", "Unknown"),
                upload_date=metadata.get("upload_date", ""),
                view_count=metadata.get("view_count", 0),
                formats=formats,
            )

        # Log cache miss
        logger.info(f"❌ Cache miss for detailed metadata: {url}")

        # Extract metadata with fallback
        start_time = time.time()
        info = await extract_metadata_with_fallback(url)
        extraction_time = time.time() - start_time

        # Extract basic metadata
        title = info.get("title", "Unknown")
        duration = float(info.get("duration", 0))
        thumbnail = info.get("thumbnail", "")
        uploader = info.get("uploader", "Unknown")
        upload_date = info.get("upload_date", "")
        view_count = int(info.get("view_count", 0))

        # Extract and filter video formats with enhanced logging
        formats = []
        seen_format_ids = set()

        logger.info(
            f"🔍 Backend: Processing {len(info.get('formats', []))} total formats from yt-dlp"
        )

        for fmt in info.get("formats", []):
            # Only include formats that have video streams (exclude audio-only)
            if (
                fmt.get("vcodec")
                and fmt.get("vcodec") != "none"
                and fmt.get("height")
                and fmt.get("width")
                and fmt.get("format_id") not in seen_format_ids
            ):
                resolution = f"{fmt.get('width')}x{fmt.get('height')}"
                format_id = fmt.get("format_id", "")

                # Avoid duplicate format IDs
                seen_format_ids.add(format_id)

                format_obj = VideoFormat(
                    format_id=format_id,
                    ext=fmt.get("ext", "mp4"),
                    resolution=resolution,
                    filesize=fmt.get("filesize"),
                    fps=fmt.get("fps"),
                    vcodec=fmt.get("vcodec", "unknown"),
                    acodec=fmt.get("acodec", "unknown"),
                    format_note=fmt.get("format_note", ""),
                )
                formats.append(format_obj)

                # Log first few formats for debugging
                if len(formats) <= 5:
                    logger.info(
                        f"🔍 Backend: Format {format_id}: {resolution} ({fmt.get('vcodec')}/{fmt.get('acodec')})"
                    )

        # Sort formats by resolution (descending), then by filesize (descending)
        def resolution_sort_key(fmt):
            try:
                width, height = map(int, fmt.resolution.split("x"))
                filesize = fmt.filesize or 0
                return (width * height, filesize)
            except (ValueError, AttributeError):
                return (0, 0)

        formats.sort(key=resolution_sort_key, reverse=True)

        # Limit to reasonable number of formats
        formats = formats[:20]

        metadata = VideoMetadata(
            title=title,
            duration=duration,
            thumbnail=thumbnail,
            uploader=uploader,
            upload_date=upload_date,
            view_count=view_count,
            formats=formats,
        )

        # Cache the detailed result using proper cache method
        detailed_metadata_to_cache = {
            "title": title,
            "duration": duration,
            "thumbnail": thumbnail,
            "uploader": uploader,
            "upload_date": upload_date,
            "view_count": view_count,
            "formats": [
                fmt.dict() for fmt in formats
            ],  # Convert to dict for JSON serialization
            "extraction_time": extraction_time,
        }

        # Use the proper cache method for format metadata
        cache_success = await cache.set_format_metadata(url, detailed_metadata_to_cache)
        if cache_success:
            logger.info(f"✅ Cached detailed metadata for: {url}")
        else:
            logger.warning(f"⚠️ Failed to cache detailed metadata for: {url}")

        logger.info(
            f"✅ Extracted detailed metadata: {title} - {len(formats)} formats in {extraction_time:.2f}s"
        )
        logger.info(
            f"🔍 Backend: Format IDs extracted: {[f.format_id for f in formats[:10]]}"
        )

        return metadata

    except DownloadError as e:
        error_str = str(e).lower()
        if "http error 429" in error_str or "too many requests" in error_str:
            logger.warning(f"YouTube blocking detected for {request.url}: {e}")
            raise HTTPException(
                status_code=429,  # Use 429 directly
                detail="YouTube is temporarily blocking requests from our server. Please try again in a few minutes.",
            )
        else:
            logger.error(f"DownloadError for {request.url}: {e}")
            raise HTTPException(
                status_code=503,
                detail="The video service is currently unavailable. Please try again later.",
            )
    except Exception as e:
        logger.error(f"❌ Failed to extract detailed metadata: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Failed to extract video metadata. The URL may be invalid or unsupported.",
        )
