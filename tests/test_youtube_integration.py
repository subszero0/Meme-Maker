import os
import asyncio
from pathlib import Path

import pytest

# Conditional import – skip tests gracefully when dependencies are missing during
# sliced CI jobs that do not install the backend or worker packages.
try:
    from backend.app.api.metadata import extract_metadata_with_fallback
    from worker.video.downloader import VideoDownloader, ProgressTracker
except ModuleNotFoundError:
    pytest.skip("Backend/worker packages not available in this environment", allow_module_level=True)

VIDEO_URL = "https://www.youtube.com/watch?v=vjFL-cBcjKc"
SHORT_URL = "https://www.youtube.com/shorts/13XuOsRzjC4"


def _yt_tests_enabled() -> bool:
    """Return True when env var ENABLE_YOUTUBE_TESTS=1 is set."""
    return os.getenv("ENABLE_YOUTUBE_TESTS", "0") == "1"


pytestmark = pytest.mark.skipif(not _yt_tests_enabled(), reason="YouTube network tests disabled. Set ENABLE_YOUTUBE_TESTS=1 to run.")


@pytest.mark.asyncio
async def test_metadata_extraction():
    info = await extract_metadata_with_fallback(VIDEO_URL)
    assert info.get("title")
    assert info.get("duration") > 0


@pytest.mark.asyncio
async def test_metadata_extraction_shorts():
    info = await extract_metadata_with_fallback(SHORT_URL)
    assert info.get("title")
    assert info.get("duration") > 0


def test_video_download(tmp_path: Path):
    tracker = ProgressTracker("test_job", None)
    downloader = VideoDownloader(tracker)

    # Download the smallest acceptable format to keep the test fast
    output_path = asyncio.run(downloader.download(VIDEO_URL, temp_dir=tmp_path))
    assert output_path.exists()
    assert output_path.stat().st_size > 500 * 1024  # >500 KB ensures not HTML 