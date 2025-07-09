import os
import asyncio
from pathlib import Path

import pytest

try:
    from backend.app.api.metadata import extract_metadata_with_fallback
    from worker.video.downloader import VideoDownloader, ProgressTracker
except ModuleNotFoundError:
    pytest.skip(
        "Backend/worker packages not available in this environment", allow_module_level=True
    )

VIDEO_URL = "https://twitter.com/i/status/1759783049371979776"


def _twitter_tests_enabled() -> bool:
    """Return True when env var ENABLE_TWITTER_TESTS=1 is set."""
    return os.getenv("ENABLE_TWITTER_TESTS", "0") == "1"


pytestmark = pytest.mark.skipif(
    not _twitter_tests_enabled(), reason="Twitter network tests disabled. Set ENABLE_TWITTER_TESTS=1 to run."
)


@pytest.mark.asyncio
async def test_metadata_extraction():
    info = await extract_metadata_with_fallback(VIDEO_URL)
    assert info.get("title")
    assert info.get("duration") and info.get("duration") > 0


def test_video_download(tmp_path: Path):
    tracker = ProgressTracker("test_job", None)
    downloader = VideoDownloader(tracker)

    output_path = asyncio.run(downloader.download(VIDEO_URL, temp_dir=tmp_path))
    assert output_path.exists()
    # Ensure file larger than 500 KB to confirm video, not HTML
    assert output_path.stat().st_size > 500 * 1024 