import pytest
from unittest import mock

from backend.app.api.metadata import extract_metadata_with_fallback


@pytest.mark.asyncio
async def test_extract_reddit_metadata_success():
    """Verify metadata extraction for Reddit video URLs works with our helper config."""
    reddit_url = "https://www.reddit.com/r/videos/comments/abc123/my_cool_clip/"

    fake_info = {
        "title": "My Reddit Video",
        "duration": 42.0,
        "thumbnail": "https://example.com/reddit-thumb.jpg",
        "uploader": "reddit_user",
        "upload_date": "20250625",
        "view_count": 9876,
        "formats": [
            {
                "format_id": "dash-720-0",
                "ext": "mp4",
                "vcodec": "avc1.4d401f",
                "acodec": "mp4a.40.2",
                "format_note": "720p",
                "url": "https://v.redd.it/abc123/DASH_720.mp4",
            }
        ],
        "manifest_url": None,
    }

    with mock.patch("yt_dlp.YoutubeDL.extract_info", return_value=fake_info):
        info = await extract_metadata_with_fallback(reddit_url)

    assert info["title"] == "My Reddit Video"
    assert info["duration"] == pytest.approx(42.0)
    assert info["formats"] 