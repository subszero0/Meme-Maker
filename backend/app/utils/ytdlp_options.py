"""
Common yt-dlp option builder used by both metadata extraction and downloader modules.
Adds:
1. Optional browser cookies (env var `YTDLP_COOKIE_FILE` or `cookies/youtube_cookies.txt`).
2. `force_ipv4` flag to avoid IPv6-specific throttling.
3. `http2` flag to mimic modern browsers.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict


def _detect_cookie_file() -> str | None:
    """Return path to cookie file if it exists, else *None*."""
    # 1. Explicit env var wins
    env_cookie = os.getenv("YTDLP_COOKIE_FILE")
    if env_cookie and Path(env_cookie).expanduser().is_file():
        return str(Path(env_cookie).expanduser())

    # 2. Conventional locations under <project_root>/cookies/
    cookies_dir = Path(__file__).resolve().parent.parent.parent.parent / "cookies"

    # Search order matters – prefer Instagram-specific cookies when present
    for candidate in [
        "instagram_cookies.txt",  # Instagram first because reels/posts frequently need auth
        "youtube_cookies.txt",  # Legacy YouTube cookies fallback
    ]:
        candidate_path = cookies_dir / candidate
        if candidate_path.is_file():
            return str(candidate_path)

    # 3. No cookie file found
    return None


def build_common_ydl_opts() -> Dict:
    """Return a dict of baseline yt-dlp options shared by backend components."""
    opts: Dict[str, object] = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        # Extra flags below make network behaviour closer to a real browser
        "force_ipv4": True,  # Mitigates some regional IPv6 throttling
        "http2": True,  # Enable HTTP/2 where supported
    }

    cookie_file = _detect_cookie_file()
    if cookie_file:
        opts["cookiefile"] = cookie_file

    return opts
