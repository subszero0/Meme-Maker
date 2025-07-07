"""
Common yt-dlp option builder for worker side.
This duplicates backend/app/utils/ytdlp_options.py to avoid cross-package import
complexities between `backend` and `worker` packages.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List


# Instagram URL detection regex
INSTAGRAM_URL_RE = re.compile(
    r"https?://(www\.)?instagram\.com/((reel|p|tv)/[\w\-]+)/?"
)


def _detect_cookie_file() -> str | None:
    env_cookie = os.getenv("YTDLP_COOKIE_FILE")
    if env_cookie and Path(env_cookie).expanduser().is_file():
        return str(Path(env_cookie).expanduser())

    fallback = Path(__file__).resolve().parent.parent / "cookies" / "youtube_cookies.txt"
    if fallback.is_file():
        return str(fallback)

    return None


def _check_browser_available() -> str | None:
    """Check if Chrome or Firefox browsers are available for cookie extraction."""
    browsers = ['chrome', 'firefox', 'chromium']
    for browser in browsers:
        try:
            # Check if browser command exists
            result = subprocess.run(['which', browser], capture_output=True, text=True)
            if result.returncode == 0:
                return browser
        except Exception:
            continue
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
    configs = []
    
    # Strategy 1: Browser cookie extraction (most effective)
    available_browser = _check_browser_available()
    if available_browser:
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
                "Referer": "https://www.instagram.com/",
            },
            "socket_timeout": 30,
            "retries": 3,
            "force_ipv4": True,
            "http2": True,
        }
        
        # Add manual cookie file if available
        cookie_file = _detect_cookie_file()
        if cookie_file:
            browser_config["cookiefile"] = cookie_file
            
        configs.append(browser_config)
    
    # Strategy 2: Mobile headers with cookie file (if available)
    mobile_config = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
            ),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.instagram.com/",
        },
        "socket_timeout": 30,
        "retries": 3,
        "force_ipv4": True,
        "http2": True,
    }
    
    cookie_file = _detect_cookie_file()
    if cookie_file:
        mobile_config["cookiefile"] = cookie_file
    
    configs.append(mobile_config)
    
    # Strategy 3: Desktop browser headers
    desktop_config = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.instagram.com/",
        },
        "socket_timeout": 45,
        "retries": 2,
        "force_ipv4": True,
        "http2": True,
    }
    
    if cookie_file:
        desktop_config["cookiefile"] = cookie_file
    
    configs.append(desktop_config)
    
    # Strategy 4: Minimal configuration (fallback)
    minimal_config = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "force_ipv4": True,
        "socket_timeout": 30,
        "retries": 1,
    }
    
    if cookie_file:
        minimal_config["cookiefile"] = cookie_file
    
    configs.append(minimal_config)
    
    return configs


def build_instagram_ydl_opts() -> Dict:
    """Build Instagram-specific yt-dlp options to avoid rate limiting and authentication issues."""
    # Return the first (most likely to succeed) configuration
    configs = build_instagram_ydl_configs()
    return configs[0] if configs else build_common_ydl_opts() 