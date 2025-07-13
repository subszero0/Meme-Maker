import asyncio
import logging
import re
import time
from typing import Dict, List, Optional

import yt_dlp
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from rq import Queue
from yt_dlp.utils import DownloadError

from ..cache.metadata_cache import MetadataCache
from ..dependencies import get_async_redis, get_clips_queue
from ..models import Job, JobCreateRequest, JobStatus
from ..utils.job_utils import generate_job_id

# Ensure yt-dlp uses any available cookies (Instagram/Youtube) across all endpoints
from ..utils.ytdlp_options import build_common_ydl_opts

router = APIRouter()
logger = logging.getLogger(__name__)

# NEW_EDIT_START: Add helper to detect Instagram URLs
INSTAGRAM_URL_RE = re.compile(
    r"https?://(www\.)?instagram\.com/((reel|p|tv)/[\w\-]+)/?"
)

# NEW_EDIT_START: Add regex for Reddit URLs
REDDIT_URL_RE = re.compile(
    r"https?://(www\.)?reddit\.com/r/[\w\-]+/comments/[\w\-]+/[\w\-]+/?|https?://v\.redd\.it/[\w\d]+"
)

# --- Job Queue ---
# Use the existing redis client to initialize the queue
# clips_queue = Queue("clips", connection=redis_client) # This line is removed


def _is_instagram_url(url: str) -> bool:
    """Return True if the provided url points to an Instagram reel / post / tv video."""
    return bool(INSTAGRAM_URL_RE.match(url))


def _is_reddit_url(url: str) -> bool:
    """Return True if the provided url points to a Reddit hosted video (post or v.redd.it)."""
    return bool(REDDIT_URL_RE.match(url))


def _process_formats_for_audio(formats: List[Dict]) -> List[Dict]:
    """
    If separate audio and video streams are detected (common in DASH),
    update video-only formats to indicate that audio will be merged.
    """
    # Check if there are any audio-only streams available
    has_audio_streams = any(
        f.get("acodec") != "none" and f.get("vcodec") == "none" for f in formats
    )

    if not has_audio_streams:
        # No separate audio streams, so return formats as-is
        return formats

    # If we are here, it means there are separate audio streams.
    # We can assume the downloader (yt-dlp) will merge the best one.
    processed_formats = []
    for f in formats:
        # If a format is video-only, but audio streams are available,
        # we can infer that audio will be included in the final download.
        if f.get("vcodec") != "none" and f.get("acodec") == "none":
            # Update the format to signal that audio is present.
            # The frontend will use this to show the correct icon.
            f["acodec"] = "aac"  # Common audio codec
            f["format_note"] = f"{f.get('format_note', '')} (audio will be merged)"

        processed_formats.append(f)

    return processed_formats


class UrlRequest(BaseModel):
    url: HttpUrl


class VideoFormat(BaseModel):
    format_id: str
    ext: str
    resolution: str
    url: str
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
    manifest_url: Optional[str] = None


def get_optimized_ydl_opts() -> Dict:
    """Get optimized yt-dlp configuration for fast metadata extraction with bot detection avoidance"""
    return {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,
        # "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", # This may be causing issues
        # "prefer_ffmpeg": True,
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
            # "extractor_args": {
            #     "youtube": {"player_client": ["tv_embedded"], "skip": ["dash", "hls"]}
            # },
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
            # "extractor_args": {
            #     "youtube": {"player_client": ["android"], "skip": ["dash"]}
            # },
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
            # "extractor_args": {
            #     "youtube": {
            #         "player_client": ["web"],
            #     }
            # },
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
    # Prepare configuration list based on the domain so that we use the most appropriate
    # headers / client hints up-front.  This improves reliability, especially for
    # platforms (like Instagram) that are sensitive to the `User-Agent` & `Referer`.

    if _is_instagram_url(url):
        instagram_base_headers = {
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
            ),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.instagram.com/",
        }

        # Start with common options so that `cookiefile` (and other shared flags) are included.
        instagram_primary_opts = {
            **build_common_ydl_opts(),  # Adds quiet, no_warnings, cookiefile, etc.
            "skip_download": True,
            "http_headers": instagram_base_headers,
            "socket_timeout": 120,  # Increased timeout for Instagram
            "retries": 5,  # Slightly more aggressive retry strategy
        }

        # For Instagram we use multiple fallback strategies to handle IP blocking
        configs = [
            instagram_primary_opts,
            {
                **instagram_primary_opts,
                "http_headers": {
                    k: v for k, v in instagram_base_headers.items() if k != "Referer"
                },
            },
            # Additional fallback with different User-Agent for IP restrictions
            {
                **instagram_primary_opts,
                "http_headers": {
                    **instagram_base_headers,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                },
                "retries": 3,
            },
            # Minimal fallback without special headers
            {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": False,
                "skip_download": True,
                "socket_timeout": 120,
                "retries": 2,
            },
        ]
    elif _is_reddit_url(url):
        # Reddit URLs are handled separately
        reddit_primary_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "skip_download": True,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
            "socket_timeout": 30,
        }
        configs = [reddit_primary_opts]
    else:
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
                        logger.info(
                            f"✅ Successfully extracted metadata with config {i+1} (retry {retry_attempt + 1})"
                        )
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
                    logger.warning(
                        f"⚠️ YouTube bot detection triggered (config {i+1}, retry {retry_attempt + 1}): {e}"
                    )

                    # If this is the last config and not the last retry, wait before retrying
                    if i == len(configs) - 1 and retry_attempt < max_retries - 1:
                        wait_time = base_wait_time * (
                            2**retry_attempt
                        )  # 30s, then 60s
                        logger.info(
                            f"🕒 YouTube rate limit detected. Waiting {wait_time}s before retry {retry_attempt + 2}/{max_retries}..."
                        )
                        logger.info(
                            "💡 This is normal for YouTube videos - we're working around temporary restrictions"
                        )
                        await asyncio.sleep(wait_time)
                        break  # Break inner loop to start next retry attempt

                    # If this is the last retry, raise the exception
                    if retry_attempt == max_retries - 1:
                        logger.error(
                            f"❌ Final retry failed after {max_retries} attempts"
                        )
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


@router.post("/metadata", response_model=Job)
async def create_clip_job(
    request: JobCreateRequest, clips_queue: Queue = Depends(get_clips_queue)
) -> Job:
    """
    Accepts a URL and optional trim times, creates a job,
    and adds it to the clips queue.
    """
    job_id = generate_job_id()
    logger.info(f"Received clip job request for url: {request.url}, job_id: {job_id}")

    job = Job(
        id=job_id,
        url=request.url,
        start_time=request.start_time,
        end_time=request.end_time,
        format_id=request.format_id,
        status=JobStatus.queued,
    )

    # Use job_id as the key for the Redis hash
    clips_queue.enqueue(
        "worker.video_processor.process_video_sync",
        job_id=job.id,
        url=str(job.url),  # Pass URL as string
        start_time=job.start_time,
        end_time=job.end_time,
        format_id=job.format_id,
        job_timeout="2h",
        result_ttl=86400,  # Keep result for 1 day
    )

    logger.info(f"Enqueued job {job.id} for processing.")
    return job


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
                title=metadata.get("title", "No Title"),
                duration=metadata.get("duration", 0),
                thumbnail=metadata.get("thumbnail", ""),
                uploader=metadata.get("uploader", "Unknown Uploader"),
                upload_date=metadata.get("upload_date", "Unknown Date"),
                view_count=metadata.get("view_count", 0),
                formats=formats,
                manifest_url=metadata.get("manifest_url"),
            )

        # Log cache miss
        logger.info(f"❌ Cache miss for detailed metadata: {url}")

        # Extract metadata with fallback
        start_time = time.time()
        info = await extract_metadata_with_fallback(url)
        extraction_time = time.time() - start_time

        # Extract basic metadata
        title = info.get("title", "No Title")
        duration = float(info.get("duration", 0))
        thumbnail_url = info.get("thumbnail", "")
        uploader = info.get("uploader", "Unknown Uploader")
        upload_date = info.get("upload_date", "Unknown Date")
        view_count = int(info.get("view_count") or 0)

        # Get available formats, ensuring it's a list
        raw_formats = info.get("formats", [])
        if not isinstance(raw_formats, list):
            raw_formats = []

        # Process formats for audio merging *before* converting to Pydantic models
        logger.info("Processing formats to check for separate audio streams...")
        processed_formats = _process_formats_for_audio(raw_formats)
        logger.info("Format processing complete.")

        # Create Pydantic models from the processed data
        video_formats = [
            VideoFormat(
                format_id=f.get("format_id", "unknown"),
                ext=f.get("ext", "unknown"),
                resolution=f.get("resolution", "unknown"),
                url=f.get("url", ""),
                filesize=f.get("filesize"),
                fps=f.get("fps"),
                vcodec=f.get("vcodec", "none"),
                acodec=f.get("acodec", "none"),
                format_note=f.get("format_note", ""),
            )
            for f in processed_formats
            if f.get("resolution")
            and f.get("vcodec") != "none"  # Only include formats with video
        ]

        # Sort formats from best to worst resolution, then by file extension
        def resolution_sort_key(fmt):
            try:
                resolution = fmt.resolution or "0x0"
                width, height = map(int, resolution.split("x"))
                filesize = fmt.filesize or 0
                return (width * height, filesize)
            except (ValueError, AttributeError):
                return (0, 0)

        video_formats.sort(key=resolution_sort_key, reverse=True)

        # Limit to reasonable number of formats
        video_formats = video_formats[:20]

        metadata = VideoMetadata(
            title=title,
            duration=duration,
            thumbnail=thumbnail_url,
            uploader=uploader,
            upload_date=upload_date,
            view_count=view_count,
            formats=video_formats,
            manifest_url=info.get("manifest_url"),
        )

        # Cache the detailed metadata
        cache_data = {
            "title": title,
            "duration": duration,
            "thumbnail": thumbnail_url,
            "uploader": uploader,
            "upload_date": upload_date,
            "view_count": view_count,
            "formats": [
                fmt.dict() for fmt in video_formats
            ],  # Convert to dict for JSON serialization
            "extraction_time": extraction_time,
            "manifest_url": info.get("manifest_url"),
        }

        # Use the proper cache method for format metadata
        cache_success = await cache.set_format_metadata(url, cache_data)
        if cache_success:
            logger.info(f"✅ Cached detailed metadata for: {url}")
        else:
            logger.warning(f"⚠️ Failed to cache detailed metadata for: {url}")

        logger.info(
            f"✅ Extracted detailed metadata: {title} - {len(video_formats)} formats in {extraction_time:.2f}s"
        )
        logger.info(
            f"🔍 Backend: Format IDs extracted: {[f.format_id for f in video_formats[:10]]}"
        )

        return metadata

    except DownloadError as e:
        error_str = str(e).lower()
        url_str = str(request.url).lower()

        # Enhanced logging for all DownloadError cases to help debug production issues
        logger.error(f"DownloadError occurred for {request.url}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Raw error message: {str(e)}")
        logger.error(f"Lowercase error message: {error_str}")

        # Instagram-specific error handling
        if "instagram.com" in url_str:
            if any(
                keyword in error_str
                for keyword in ["login", "authentication", "cookies", "sign in"]
            ):
                logger.warning(
                    f"Instagram authentication required for {request.url}: {e}"
                )
                raise HTTPException(
                    status_code=429,
                    detail="Instagram requires authentication for this content. Please try again later or use a different URL.",
                )
            elif "timeout" in error_str or "timed out" in error_str:
                logger.warning(f"Instagram timeout for {request.url}: {e}")
                raise HTTPException(
                    status_code=504,
                    detail="Instagram is taking too long to respond. Please try again in a moment.",
                )
            elif any(
                keyword in error_str
                for keyword in [
                    "private",
                    "unavailable",
                    "not found",
                    "does not exist",
                    "blocked",
                    "restricted",
                ]
            ):
                logger.warning(f"Instagram content unavailable for {request.url}: {e}")
                raise HTTPException(
                    status_code=422,
                    detail="This Instagram content is private, unavailable, or restricted in your region. Please try a different URL.",
                )
            else:
                # Enhanced logging for unhandled Instagram errors
                logger.error(f"Unhandled Instagram error for {request.url}: {e}")
                logger.error(f"Error type: {type(e).__name__}")
                logger.error(f"Full error message: {str(e)}")
                raise HTTPException(
                    status_code=503,
                    detail="Instagram content temporarily unavailable. This may be due to regional restrictions or temporary blocking. Please try again later or use a different URL.",
                )

        # YouTube-specific error handling
        if "http error 429" in error_str or "too many requests" in error_str:
            logger.warning(f"Rate limiting detected for {request.url}: {e}")
            raise HTTPException(
                status_code=429,
                detail="Too many requests to the video service. Please try again in a few minutes.",
            )
        elif "timeout" in error_str or "timed out" in error_str:
            logger.warning(f"Timeout error for {request.url}: {e}")
            raise HTTPException(
                status_code=504,
                detail="The video service is taking too long to respond. Please try again.",
            )
        else:
            logger.error(f"DownloadError for {request.url}: {e}")
            raise HTTPException(
                status_code=503,
                detail="The video service is currently unavailable. Please try again later.",
            )
    except Exception as e:
        logger.error(f"❌ yt-dlp failed to extract info for {url}: {e}")
        # Log the full exception for debugging
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=404, detail=f"Failed to extract video metadata: {e}"
        )


@router.post("/metadata/cached", response_model=VideoMetadata)
async def get_cached_video_metadata(
    request: UrlRequest, redis_client=Depends(get_async_redis)
):
    """Get cached video metadata"""
    try:
        url = str(request.url)
        logger.info(f"🔍 Fetching cached metadata for: {url}")

        # Initialize cache
        cache = MetadataCache(redis_client)

        # Check cache first
        cached_metadata = await cache.get_format_metadata(url)
        if cached_metadata:
            logger.info(f"✅ Cache hit for cached metadata: {url}")
            metadata = cached_metadata.get("metadata", {})

            # Reconstruct VideoFormat objects
            formats = []
            for fmt_data in metadata.get("formats", []):
                formats.append(VideoFormat(**fmt_data))

            return VideoMetadata(
                title=metadata.get("title", "No Title"),
                duration=metadata.get("duration", 0),
                thumbnail=metadata.get("thumbnail", ""),
                uploader=metadata.get("uploader", "Unknown Uploader"),
                upload_date=metadata.get("upload_date", "Unknown Date"),
                view_count=metadata.get("view_count", 0),
                formats=formats,
                manifest_url=metadata.get("manifest_url"),
            )

        # Log cache miss
        logger.info(f"❌ Cache miss for cached metadata: {url}")
        raise HTTPException(status_code=404, detail="Video metadata not found")

    except Exception as e:
        logger.error(f"❌ Failed to fetch cached metadata: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected server error occurred while fetching cached metadata.",
        )
