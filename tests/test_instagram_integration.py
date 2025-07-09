from unittest import mock

import pytest

# Import the function we want to test
from backend.app.api.metadata import extract_metadata_with_fallback


@pytest.mark.asyncio
async def test_extract_instagram_metadata_success():
    """Ensure the metadata extractor can process an Instagram reel/post URL."""
    # Example Instagram reel URL (structure only – no network will be called because we mock)
    ig_url = "https://www.instagram.com/reel/CRkAhn8Dkfo/"

    # Build a fake response that mimics yt-dlp's extract_info output for Instagram
    fake_info = {
        "title": "My Awesome Reel",
        "duration": 12.34,
        "thumbnail": "https://example.com/thumb.jpg",
        "uploader": "my_ig_user",
        "upload_date": "20250625",
        "view_count": 12345,
        "formats": [
            {
                "format_id": "0",
                "ext": "mp4",
                "vcodec": "avc1.64001F",
                "acodec": "mp4a.40.2",
                "format_note": "720p",
                "url": "https://example.com/video.mp4",
                "filesize": 3_000_000,
            }
        ],
        "manifest_url": None,
    }

    # Patch the internal yt_dlp call so no external network is used
    with mock.patch("yt_dlp.YoutubeDL.extract_info", return_value=fake_info):
        info = await extract_metadata_with_fallback(ig_url)

    assert info["title"] == "My Awesome Reel"
    assert info["duration"] == pytest.approx(12.34, rel=1e-2)
    assert len(info["formats"]) > 0 