"""
Platform detection utilities for video URL analysis and format mapping.
Provides platform-specific format ID mapping for resolution selection.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Optional, Tuple


class Platform(Enum):
    """Supported video platforms."""

    YOUTUBE = "youtube"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    UNKNOWN = "unknown"


class PlatformDetector:
    """Detect video platform from URL and provide format mapping."""

    # Platform URL patterns
    _PLATFORM_PATTERNS = {
        Platform.YOUTUBE: [
            r"(?:https?://)(?:www\.)?(?:youtube\.com|youtu\.be)",
            r"(?:https?://)(?:m\.)?youtube\.com",
        ],
        Platform.FACEBOOK: [
            r"(?:https?://)(?:www\.)?facebook\.com",
            r"(?:https?://)(?:www\.)?fb\.watch",
        ],
        Platform.INSTAGRAM: [
            r"(?:https?://)(?:www\.)?instagram\.com",
        ],
        Platform.TIKTOK: [
            r"(?:https?://)(?:www\.)?tiktok\.com",
            r"(?:https?://)(?:vm\.)?tiktok\.com",
        ],
    }

    # Platform-specific format mapping (resolution -> format_id)
    _PLATFORM_FORMAT_MAP = {
        Platform.YOUTUBE: {
            "144p": "160",  # MP4 144p
            "240p": "133",  # MP4 240p
            "360p": "134",  # MP4 360p
            "480p": "135",  # MP4 480p
            "720p": "136",  # MP4 720p
            "1080p": "137",  # MP4 1080p
            "1440p": "271",  # MP4 1440p
            "2160p": "313",  # MP4 2160p (4K)
        },
        Platform.FACEBOOK: {
            "360p": "dash_sd_src",
            "480p": "dash_sd_src",
            "720p": "dash_hd_src",
            "1080p": "dash_hd_src",
        },
        Platform.INSTAGRAM: {
            "360p": "mp4",
            "480p": "mp4",
            "720p": "mp4",
            "1080p": "mp4",
        },
        Platform.TIKTOK: {
            "360p": "mp4",
            "480p": "mp4",
            "720p": "mp4",
            "1080p": "mp4",
        },
    }

    # Default fallback format when specific resolution not available
    _PLATFORM_FALLBACK = {
        Platform.YOUTUBE: "best[height<=720]/best",
        Platform.FACEBOOK: "best[height<=720]/best",
        Platform.INSTAGRAM: "best[height<=720]/best",
        Platform.TIKTOK: "best[height<=720]/best",
        Platform.UNKNOWN: "best[height<=720]/best",
    }

    @classmethod
    def detect_platform(cls, url: str) -> Platform:
        """
        Detect the video platform from URL.

        Args:
            url: Video URL to analyze

        Returns:
            Platform enum value
        """
        url_lower = url.lower()

        for platform, patterns in cls._PLATFORM_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url_lower):
                    return platform

        return Platform.UNKNOWN

    @classmethod
    def map_resolution_to_format_id(
        cls, platform: Platform, resolution: str
    ) -> Optional[str]:
        """
        Map resolution string to platform-specific format ID.

        Args:
            platform: Video platform
            resolution: Resolution string (e.g., "720p")

        Returns:
            Format ID string or None if not available
        """
        platform_map = cls._PLATFORM_FORMAT_MAP.get(platform, {})
        return platform_map.get(resolution)

    @classmethod
    def get_fallback_format(cls, platform: Platform) -> str:
        """
        Get fallback format selector for platform.

        Args:
            platform: Video platform

        Returns:
            Format selector string for yt-dlp
        """
        return cls._PLATFORM_FALLBACK.get(
            platform, cls._PLATFORM_FALLBACK[Platform.UNKNOWN]
        )

    @classmethod
    def resolve_format_id(
        cls, url: str, resolution: Optional[str] = None
    ) -> Tuple[Platform, Optional[str]]:
        """
        Resolve URL and resolution to format ID.

        Args:
            url: Video URL
            resolution: Requested resolution (optional)

        Returns:
            Tuple of (platform, format_id) where format_id may be None
        """
        platform = cls.detect_platform(url)

        if not resolution:
            return platform, None

        format_id = cls.map_resolution_to_format_id(platform, resolution)
        return platform, format_id

    @classmethod
    def get_effective_format_selector(
        cls, url: str, resolution: Optional[str] = None, format_id: Optional[str] = None
    ) -> str:
        """
        Get the effective format selector for yt-dlp.

        Priority:
        1. Explicit format_id (if provided)
        2. Platform-mapped format_id from resolution
        3. Platform fallback selector

        Args:
            url: Video URL
            resolution: Requested resolution (optional)
            format_id: Explicit format ID (optional)

        Returns:
            Format selector string for yt-dlp
        """
        platform = cls.detect_platform(url)

        # Priority 1: Explicit format_id
        if format_id and format_id != "None":
            return format_id

        # Priority 2: Map resolution to format_id
        if resolution:
            mapped_format_id = cls.map_resolution_to_format_id(platform, resolution)
            if mapped_format_id:
                return mapped_format_id

        # Priority 3: Platform fallback
        return cls.get_fallback_format(platform)
