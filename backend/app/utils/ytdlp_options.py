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

    # NEW: Instagram and Facebook cookie content passed in environment variables

    import base64
    import logging
    import tempfile

    logger = logging.getLogger(__name__)

    # Check for base64 encoded Instagram cookie content in environment variable
    env_cookie_b64 = os.getenv("INSTAGRAM_COOKIES_B64")
    if env_cookie_b64:
        try:
            cookie_content = base64.b64decode(env_cookie_b64).decode("utf-8")
            temp_dir = Path(tempfile.gettempdir())
            temp_cookie_file = temp_dir / "instagram_cookies_temp.txt"
            temp_cookie_file.write_text(cookie_content)
            logger.info(
                f"✅ Created temporary cookie file from INSTAGRAM_COOKIES_B64 env var: {temp_cookie_file}"
            )
            return str(temp_cookie_file)
        except Exception as e:
            logger.warning(
                f"⚠️ Failed to decode INSTAGRAM_COOKIES_B64 env var into cookie file: {e}"
            )

    # Check for base64 encoded Facebook cookie content in environment variable
    facebook_cookie_b64 = os.getenv("FACEBOOK_COOKIES_B64")
    if facebook_cookie_b64:
        try:
            cookie_content = base64.b64decode(facebook_cookie_b64).decode("utf-8")
            temp_dir = Path(tempfile.gettempdir())
            temp_cookie_file = temp_dir / "facebook_cookies_temp.txt"
            temp_cookie_file.write_text(cookie_content)
            logger.info(
                f"✅ Created temporary cookie file from FACEBOOK_COOKIES_B64 env var: {temp_cookie_file}"
            )
            return str(temp_cookie_file)
        except Exception as e:
            logger.warning(
                f"⚠️ Failed to decode FACEBOOK_COOKIES_B64 env var into cookie file: {e}"
            )

    # Check for plain text Instagram cookie content in env variable
    env_cookie_content = os.getenv("INSTAGRAM_COOKIES")
    if env_cookie_content:
        try:
            temp_dir = Path(tempfile.gettempdir())
            temp_cookie_file = temp_dir / "instagram_cookies_temp.txt"
            temp_cookie_file.write_text(env_cookie_content)
            logger.info(
                f"✅ Created temporary cookie file from INSTAGRAM_COOKIES env var: {temp_cookie_file}"
            )
            return str(temp_cookie_file)
        except Exception as e:
            logger.warning(
                f"⚠️ Failed to write INSTAGRAM_COOKIES env var into cookie file: {e}"
            )

    # Check for plain text Facebook cookie content in env variable
    facebook_cookie_content = os.getenv("FACEBOOK_COOKIES")
    if facebook_cookie_content:
        try:
            temp_dir = Path(tempfile.gettempdir())
            temp_cookie_file = temp_dir / "facebook_cookies_temp.txt"
            temp_cookie_file.write_text(facebook_cookie_content)
            logger.info(
                f"✅ Created temporary cookie file from FACEBOOK_COOKIES env var: {temp_cookie_file}"
            )
            return str(temp_cookie_file)
        except Exception as e:
            logger.warning(
                f"⚠️ Failed to write FACEBOOK_COOKIES env var into cookie file: {e}"
            )

    # 2. Conventional locations under <project_root>/cookies/
    cookies_dir = Path(__file__).resolve().parent.parent.parent.parent / "cookies"

    # Search order matters – prefer platform-specific cookies when present
    for candidate in [
        "facebook_cookies.txt",  # Facebook cookies
        "instagram_cookies.txt",  # Instagram cookies
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
