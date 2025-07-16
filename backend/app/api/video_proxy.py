import logging

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/proxy")
async def proxy_video(url: str, request: Request):
    """
    Proxy video content through our backend to bypass CORS restrictions.
    This allows the frontend to play Instagram/Facebook videos that would
    otherwise be blocked by CORS policies.
    """
    logger.info(f"🔍 Video proxy request received for URL: {url[:100]}...")

    try:
        # Validate URL (basic security check) - Updated for Instagram and Facebook CDN domains
        allowed_domains = (
            "https://instagram.",
            "https://www.instagram.",
            "https://fb.watch/",
            "https://facebook.",
            "https://www.facebook.",
            "https://scontent.",
            "https://scontent-",  # Instagram/Facebook CDN (scontent-lax3-1.cdninstagram.com, etc.)
            "https://video-",  # Instagram/Facebook video CDN
            "https://instagramstatic-",  # Instagram static CDN
            "https://instagram.f",  # Instagram fbcdn.net CDN (instagram.fdel8-2.fna.fbcdn.net, etc.)
            "https://lookaside.fbsbx.com/",  # Facebook image/video CDN
            "https://video.",  # Facebook video CDN (video.xx.fbcdn.net)
            "https://video.f",  # Facebook video CDN (video.fxxx-x.fna.fbcdn.net)
            "https://external-",  # Facebook external CDN
            "https://fbcdn.net/",  # Facebook CDN domains
            "https://graph.facebook.com/",  # Facebook Graph API
        )

        logger.info(f"🔍 Checking domain validation for: {url[:50]}...")
        if not url.startswith(allowed_domains):
            logger.warning(f"❌ Rejected URL with invalid domain: {url[:100]}")
            raise HTTPException(status_code=400, detail="Invalid video URL domain")

        logger.info(f"✅ Accepted URL for proxying: {url[:100]}...")

        # Set up headers to mimic a legitimate request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "identity",  # Don't compress for streaming
            "Sec-Fetch-Dest": "video",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
        }

        logger.info(f"🌐 Making request to: {url[:100]}...")

        # Handle range requests for video seeking
        range_header = request.headers.get("range")
        if range_header:
            headers["Range"] = range_header
            logger.info(f"📋 Range request: {range_header}")

        logger.info("🔗 Creating httpx client...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info("📡 Making GET request...")
            response = await client.get(url, headers=headers, follow_redirects=True)
            logger.info(f"📡 Received response: {response.status_code}")

            if response.status_code not in [200, 206]:  # 206 for partial content
                logger.error(
                    f"❌ Video proxy failed: {response.status_code} {response.text}"
                )
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch video: {response.status_code}",
                )

            logger.info("✅ Preparing response headers...")
            # Prepare response headers
            response_headers = {
                "Content-Type": response.headers.get("content-type", "video/mp4"),
                "Accept-Ranges": "bytes",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
                "Access-Control-Allow-Headers": "Range, Content-Type",
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
            }

            # Include content-length and range headers if present
            if "content-length" in response.headers:
                response_headers["Content-Length"] = response.headers["content-length"]

            if "content-range" in response.headers:
                response_headers["Content-Range"] = response.headers["content-range"]

            logger.info(
                f"✅ Video proxy successful: {response.status_code}, Content-Type: {response_headers['Content-Type']}"
            )

            # Stream the video content
            async def generate():
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    yield chunk

            return StreamingResponse(
                generate(),
                status_code=response.status_code,
                headers=response_headers,
                media_type=response_headers["Content-Type"],
            )

    except httpx.TimeoutException as e:
        logger.error(f"❌ Video proxy timeout: {e}")
        raise HTTPException(status_code=504, detail="Video request timeout")
    except httpx.RequestError as e:
        logger.error(f"❌ Video proxy request error: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch video")
    except HTTPException:
        # Re-raise HTTP exceptions (like domain validation errors)
        raise
    except Exception as e:
        logger.error(f"❌ Video proxy unexpected error: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback

        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/test")
async def test_proxy():
    """Simple test endpoint to verify the proxy router is working"""
    logger.info("🧪 Test endpoint called")
    return {"message": "Video proxy router is working", "status": "ok"}


@router.options("/proxy")
async def proxy_video_options():
    """Handle CORS preflight requests for video proxy"""
    return Response(
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "Range, Content-Type",
            "Access-Control-Max-Age": "86400",
        }
    )
