import ipaddress
import logging
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse

from ..config.configuration import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


def validate_url_for_ssrf(url: str) -> bool:
    """
    Comprehensive SSRF protection for video proxy URLs
    """
    try:
        parsed = urlparse(url)

        # Must be HTTPS
        if parsed.scheme != "https":
            logger.warning(
                f"❌ SSRF Protection: Non-HTTPS scheme rejected: {parsed.scheme}"
            )
            return False

        # Must have a hostname
        if not parsed.hostname:
            logger.warning("❌ SSRF Protection: No hostname in URL")
            return False

        # Block private/local IP addresses
        try:
            ip = ipaddress.ip_address(parsed.hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                logger.warning(f"❌ SSRF Protection: Private/local IP rejected: {ip}")
                return False
        except ValueError:
            # Not an IP address, continue with domain validation
            pass

        # Block localhost and local domains
        blocked_hostnames = [
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "[::]",
            "[::1]",
            "metadata.google.internal",
            "169.254.169.254",  # Cloud metadata
            "internal",
            "local",
            ".local",
        ]

        hostname_lower = parsed.hostname.lower()
        for blocked in blocked_hostnames:
            if blocked in hostname_lower:
                logger.warning(
                    f"❌ SSRF Protection: Blocked hostname: {hostname_lower}"
                )
                return False

        # Only allow specific trusted domains for video content
        allowed_domains = [
            "instagram.com",
            "www.instagram.com",
            "facebook.com",
            "www.facebook.com",
            "fb.watch",
            "scontent.cdninstagram.com",
            "scontent-",  # Instagram CDN
            "fbcdn.net",
            "lookaside.fbsbx.com",  # Facebook CDN
            "youtube.com",
            "www.youtube.com",
            "youtu.be",  # YouTube (if needed)
            "googlevideo.com",  # YouTube CDN
        ]

        # Check if hostname matches allowed domains
        hostname_allowed = False
        for domain in allowed_domains:
            if domain.startswith("scontent-"):  # Special case for Instagram CDN
                if (
                    hostname_lower.startswith("scontent-")
                    and ".cdninstagram.com" in hostname_lower
                ):
                    hostname_allowed = True
                    break
            elif hostname_lower == domain or hostname_lower.endswith("." + domain):
                hostname_allowed = True
                break

        if not hostname_allowed:
            logger.warning(
                f"❌ SSRF Protection: Domain not in allowlist: {hostname_lower}"
            )
            return False

        # Additional checks for port (should be standard HTTPS)
        if parsed.port and parsed.port != 443:
            logger.warning(
                f"❌ SSRF Protection: Non-standard port rejected: {parsed.port}"
            )
            return False

        logger.info(f"✅ SSRF Protection: URL validated successfully: {hostname_lower}")
        return True

    except Exception as e:
        logger.error(f"❌ SSRF Protection: URL validation error: {e}")
        return False


@router.get("/proxy")
async def proxy_video(url: str, request: Request):
    """
    Proxy video content through our backend to bypass CORS restrictions.
    This allows the frontend to play Instagram/Facebook videos that would
    otherwise be blocked by CORS policies.
    """
    logger.info(f"🔍 Video proxy request received for URL: {url[:100]}...")

    try:
        # Comprehensive SSRF protection
        if not validate_url_for_ssrf(url):
            logger.warning(f"❌ SSRF Protection: URL validation failed: {url[:100]}")
            raise HTTPException(
                status_code=400,
                detail="Invalid video URL: URL failed security validation",
            )

        logger.info(f"✅ URL passed SSRF validation: {url[:100]}...")

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


# Test endpoint - only available in development/staging environments
if settings.environment != "production":

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
