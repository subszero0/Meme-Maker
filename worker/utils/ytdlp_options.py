"""
Common yt-dlp option builder for worker side.
This duplicates backend/app/utils/ytdlp_options.py to avoid cross-package import
complexities between `backend` and `worker` packages.
"""
from __future__ import annotations

import os
import re
import subprocess
import logging
from pathlib import Path
from typing import Dict, List

# Set up logging
logger = logging.getLogger(__name__)

# Instagram URL detection regex
INSTAGRAM_URL_RE = re.compile(
    r"https?://(www\.)?instagram\.com/((reel|p|tv)/[\w\-]+)/?"
)


def _detect_cookie_file() -> str | None:
    """Detect available cookie files for yt-dlp authentication."""
    logger.info("🍪 Detecting cookie files...")

    # NEW: Check for base64 encoded Instagram cookie content in environment variable
    env_cookie_b64 = os.getenv("INSTAGRAM_COOKIES_B64")
    if env_cookie_b64:
        try:
            import base64
            import tempfile
            
            # Decode the base64 content
            cookie_content = base64.b64decode(env_cookie_b64).decode('utf-8')
            
            # Create a temporary cookie file from decoded content
            temp_dir = Path("/tmp")
            temp_dir.mkdir(exist_ok=True)
            temp_cookie_file = temp_dir / "instagram_cookies_temp.txt"
            
            # Write the cookie content to the temporary file
            with open(temp_cookie_file, 'w') as f:
                f.write(cookie_content)
            
            logger.info(f"✅ Created temporary cookie file from Instagram base64 environment variable: {temp_cookie_file}")
            return str(temp_cookie_file)
        except Exception as e:
            logger.warning(f"⚠️ Failed to create temporary cookie file from Instagram base64 env var: {e}")

    # NEW: Check for base64 encoded Facebook cookie content in environment variable
    facebook_cookie_b64 = os.getenv("FACEBOOK_COOKIES_B64")
    if facebook_cookie_b64:
        try:
            import base64
            import tempfile
            
            # Decode the base64 content
            cookie_content = base64.b64decode(facebook_cookie_b64).decode('utf-8')
            
            # Create a temporary cookie file from decoded content
            temp_dir = Path("/tmp")
            temp_dir.mkdir(exist_ok=True)
            temp_cookie_file = temp_dir / "facebook_cookies_temp.txt"
            
            # Write the cookie content to the temporary file
            with open(temp_cookie_file, 'w') as f:
                f.write(cookie_content)
            
            logger.info(f"✅ Created temporary cookie file from Facebook base64 environment variable: {temp_cookie_file}")
            return str(temp_cookie_file)
        except Exception as e:
            logger.warning(f"⚠️ Failed to create temporary cookie file from Facebook base64 env var: {e}")

    # NEW: Check for Instagram cookie content in environment variable first
    env_cookie_content = os.getenv("INSTAGRAM_COOKIES")
    if env_cookie_content:
        try:
            # Create a temporary cookie file from environment variable content
            import tempfile
            temp_dir = Path("/tmp")
            temp_dir.mkdir(exist_ok=True)
            temp_cookie_file = temp_dir / "instagram_cookies_temp.txt"
            
            # Write the cookie content to the temporary file
            with open(temp_cookie_file, 'w') as f:
                f.write(env_cookie_content)
            
            logger.info(f"✅ Created temporary cookie file from Instagram environment variable: {temp_cookie_file}")
            return str(temp_cookie_file)
        except Exception as e:
            logger.warning(f"⚠️ Failed to create temporary cookie file from Instagram env var: {e}")

    # NEW: Check for Facebook cookie content in environment variable
    facebook_cookie_content = os.getenv("FACEBOOK_COOKIES")
    if facebook_cookie_content:
        try:
            # Create a temporary cookie file from environment variable content
            import tempfile
            temp_dir = Path("/tmp")
            temp_dir.mkdir(exist_ok=True)
            temp_cookie_file = temp_dir / "facebook_cookies_temp.txt"
            
            # Write the cookie content to the temporary file
            with open(temp_cookie_file, 'w') as f:
                f.write(facebook_cookie_content)
            
            logger.info(f"✅ Created temporary cookie file from Facebook environment variable: {temp_cookie_file}")
            return str(temp_cookie_file)
        except Exception as e:
            logger.warning(f"⚠️ Failed to create temporary cookie file from Facebook env var: {e}")

    # Check environment variable for file path
    env_cookie = os.getenv("YTDLP_COOKIE_FILE")
    if env_cookie:
        expanded_path = Path(env_cookie).expanduser()
        if expanded_path.is_file():
            logger.info(f"✅ Found cookie file from env var: {expanded_path}")
            return str(expanded_path)
        else:
            logger.warning(f"⚠️ Cookie file from env var not found: {expanded_path}")

    # Check for Facebook-specific cookies
    facebook_cookies = (
        Path(__file__).resolve().parent.parent / "cookies" / "facebook_cookies.txt"
    )
    if facebook_cookies.is_file():
        logger.info(f"✅ Found Facebook-specific cookies: {facebook_cookies}")
        return str(facebook_cookies)

    # Check for Instagram-specific cookies
    instagram_cookies = (
        Path(__file__).resolve().parent.parent / "cookies" / "instagram_cookies.txt"
    )
    if instagram_cookies.is_file():
        logger.info(f"✅ Found Instagram-specific cookies: {instagram_cookies}")
        return str(instagram_cookies)

    # Check for generic cookies
    fallback = (
        Path(__file__).resolve().parent.parent / "cookies" / "youtube_cookies.txt"
    )
    if fallback.is_file():
        logger.info(f"✅ Found fallback cookie file: {fallback}")
        return str(fallback)

    logger.warning(
        "⚠️ No cookie files found. This may affect Instagram/Facebook download success."
    )
    return None


def _check_browser_available() -> str | None:
    """Check if Chrome or Firefox browsers are available for cookie extraction."""
    logger.info("🔍 Checking for available browsers...")
    browsers = ["chrome", "firefox", "chromium", "google-chrome"]

    for browser in browsers:
        try:
            # Check if browser command exists
            result = subprocess.run(
                ["which", browser], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                browser_path = result.stdout.strip()
                logger.info(f"✅ Found browser '{browser}' at: {browser_path}")
                return browser
            else:
                logger.debug(f"❌ Browser '{browser}' not found")
        except subprocess.TimeoutExpired:
            logger.warning(f"⚠️ Timeout checking for browser '{browser}'")
        except Exception as e:
            logger.debug(f"❌ Error checking browser '{browser}': {e}")

    logger.warning(
        "⚠️ No browsers found for cookie extraction. This may limit Instagram access."
    )
    return None


def is_instagram_url(url: str) -> bool:
    """Return True if the provided url points to an Instagram reel / post / tv video."""
    return bool(INSTAGRAM_URL_RE.match(url))


def build_common_ydl_opts() -> Dict:
    opts: Dict[str, object] = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "force_ipv4": True,
        "http2": True,
    }
    cookie_file = _detect_cookie_file()
    if cookie_file:
        opts["cookiefile"] = cookie_file
    return opts


def build_instagram_ydl_configs() -> List[Dict]:
    """Build multiple Instagram yt-dlp configurations for fallback strategies."""
    logger.info("🎬 Building Instagram download configurations...")
    configs = []

    # Check available resources
    available_browser = _check_browser_available()
    cookie_file = _detect_cookie_file()

    # --- NEW: Strategy 1: Prioritize Cookie File ---
    if cookie_file:
        logger.info("📋 Strategy 1: Using dedicated cookie file")
        cookie_config = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "cookiefile": cookie_file,
            "force_ipv4": True,
            "http2": True,
            "retries": 2,  # Fewer retries needed if cookies are valid
            "socket_timeout": 30,
        }
        configs.append(cookie_config)
    else:
        logger.info("📋 Strategy 1: Skipped (no cookie file found)")

    # Strategy 2: Browser cookie extraction (if available)
    if available_browser:
        logger.info(
            f"📋 Strategy 2: Browser cookie extraction using {available_browser}"
        )
        browser_config = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "cookiesfrombrowser": (available_browser, None),
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
                ),
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Referer": "https://www.instagram.com/",
                "Origin": "https://www.instagram.com",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
            },
            "socket_timeout": 30,
            "retries": 3,
            "force_ipv4": True,
            "http2": True,
        }

        # Add manual cookie file if available
        if cookie_file:
            browser_config["cookiefile"] = cookie_file

        configs.append(browser_config)
    else:
        logger.info("📋 Strategy 2: Skipped (no browser available)")

    # Strategy 3: Enhanced mobile headers
    logger.info("📋 Strategy 3: Enhanced mobile headers")
    mobile_config = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Mobile/15E148 Safari/604.1"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Referer": "https://www.instagram.com/",
            "Origin": "https://www.instagram.com",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        },
        "socket_timeout": 45,
        "retries": 4,
        "force_ipv4": True,
        "http2": True,
        "sleep_interval": 1,
        "max_sleep_interval": 5,
    }

    if cookie_file:
        mobile_config["cookiefile"] = cookie_file

    configs.append(mobile_config)

    # Strategy 4: Enhanced desktop browser headers
    logger.info("📋 Strategy 4: Enhanced desktop headers")
    desktop_config = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
            "Referer": "https://www.instagram.com/",
            "Origin": "https://www.instagram.com",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
        },
        "socket_timeout": 60,
        "retries": 3,
        "force_ipv4": True,
        "http2": True,
        "sleep_interval": 2,
        "max_sleep_interval": 8,
    }

    if cookie_file:
        desktop_config["cookiefile"] = cookie_file

    configs.append(desktop_config)

    # Strategy 5: Simplified fallback with minimal headers
    logger.info("📋 Strategy 5: Simplified fallback")
    simple_config = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.instagram.com/",
        },
        "force_ipv4": True,
        "socket_timeout": 30,
        "retries": 2,
        "sleep_interval": 1,
    }

    if cookie_file:
        simple_config["cookiefile"] = cookie_file

    configs.append(simple_config)

    # Strategy 6: No headers (last resort)
    logger.info("📋 Strategy 6: No headers (last resort)")
    no_header_config = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "force_ipv4": True,
        "socket_timeout": 45,
        "retries": 1,
    }

    if cookie_file:
        no_header_config["cookiefile"] = cookie_file

    configs.append(no_header_config)

    logger.info(f"✅ Built {len(configs)} Instagram configurations")
    return configs


def build_instagram_ydl_opts() -> Dict:
    """Build Instagram-specific yt-dlp options to avoid rate limiting and authentication issues."""
    # Return the first (most likely to succeed) configuration
    configs = build_instagram_ydl_configs()
    return configs[0] if configs else build_common_ydl_opts()
