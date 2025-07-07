"""
Common yt-dlp option builder for worker side.
This duplicates backend/app/utils/ytdlp_options.py to avoid cross-package import
complexities between `backend` and `worker` packages.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict


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


def build_instagram_ydl_opts() -> Dict:
    """Build Instagram-specific yt-dlp options to avoid rate limiting and authentication issues."""
    instagram_headers = {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        ),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.instagram.com/",
    }
    
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "http_headers": instagram_headers,
        "socket_timeout": 30,
        "retries": 3,
        "force_ipv4": True,
        "http2": True,
    }
    
    # Add cookies if available
    cookie_file = _detect_cookie_file()
    if cookie_file:
        opts["cookiefile"] = cookie_file
    
    return opts 