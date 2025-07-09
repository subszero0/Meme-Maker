#!/usr/bin/env python3
"""
Diagnostic script to test yt-dlp functionality and identify YouTube download issues
"""
import os
import sys
import tempfile
import logging
import subprocess
from pathlib import Path

import yt_dlp

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_ytdlp_version():
    """Test yt-dlp version and update status"""
    try:
        # Get current version
        result = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True)
        current_version = result.stdout.strip() if result.returncode == 0 else "Unknown"
        logger.info(f"Current yt-dlp version: {current_version}")

        # Try to update
        logger.info("Attempting to update yt-dlp...")
        update_result = subprocess.run(["yt-dlp", "-U"], capture_output=True, text=True)
        logger.info(f"Update result: {update_result.stdout.strip()}")

        # Check version after update
        result = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True)
        new_version = result.stdout.strip() if result.returncode == 0 else "Unknown"
        logger.info(f"Version after update: {new_version}")

    except Exception as e:
        logger.error(f"Error checking yt-dlp version: {e}")


def test_simple_extraction(url: str):
    """Test simple info extraction without downloading"""
    logger.info(f"Testing info extraction for: {url}")

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if "entries" in info and info["entries"]:
                info = info["entries"][0]

            logger.info(f"Title: {info.get('title', 'Unknown')}")
            logger.info(f"Duration: {info.get('duration', 'Unknown')} seconds")
            logger.info(f"Available formats: {len(info.get('formats', []))}")

            # Show some format details
            formats = info.get("formats", [])[:5]  # First 5 formats
            for i, fmt in enumerate(formats):
                logger.info(
                    f"Format {i}: {fmt.get('format_id')} - {fmt.get('ext')} - {fmt.get('resolution', 'audio')} - {fmt.get('filesize_approx', 'Unknown size')}"
                )

            return True
    except Exception as e:
        logger.error(f"Info extraction failed: {e}")
        return False


def test_download_with_configs(url: str):
    """Test downloading with different configurations"""
    with tempfile.TemporaryDirectory(prefix="ytdlp_test_") as temp_dir:
        temp_path = Path(temp_dir)

        # Test configurations
        configs = [
            {
                "name": "Android Client",
                "opts": {
                    "outtmpl": str(temp_path / "test_android.%(ext)s"),
                    "format": "best[ext=mp4][height<=720]/best[height<=720]/best[ext=mp4]/best",
                    "quiet": True,
                    "no_warnings": True,
                    "writesubtitles": False,
                    "writeautomaticsub": False,
                    "extractor_args": {
                        "youtube": {
                            "player_client": ["android"],
                            "skip": ["dash", "hls"],
                        }
                    },
                    "http_headers": {
                        "User-Agent": "com.google.android.youtube/17.31.35 (Linux; U; Android 11) gzip"
                    },
                },
            },
            {
                "name": "Web Client",
                "opts": {
                    "outtmpl": str(temp_path / "test_web.%(ext)s"),
                    "format": "best[ext=mp4][height<=480]/best[height<=480]/worst[ext=mp4]/worst",
                    "quiet": True,
                    "no_warnings": True,
                    "writesubtitles": False,
                    "writeautomaticsub": False,
                    "http_headers": {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                },
            },
            {
                "name": "Latest Format (Updated)",
                "opts": {
                    "outtmpl": str(temp_path / "test_latest.%(ext)s"),
                    "format": "best[height<=720]/best",
                    "quiet": False,
                    "no_warnings": False,
                    "writesubtitles": False,
                    "writeautomaticsub": False,
                    "extractor_args": {
                        "youtube": {
                            "player_client": ["web", "android"],
                        }
                    },
                    "http_headers": {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    },
                },
            },
        ]

        for config in configs:
            logger.info(f"\n=== Testing {config['name']} ===")
            try:
                with yt_dlp.YoutubeDL(config["opts"]) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if "entries" in info and info["entries"]:
                        info = info["entries"][0]

                # Check downloaded files
                downloaded_files = list(temp_path.glob("test_*"))
                if downloaded_files:
                    for file in downloaded_files:
                        file_size = file.stat().st_size
                        logger.info(
                            f"✅ Downloaded: {file.name} ({file_size} bytes, {file.suffix})"
                        )

                        # Check if it's actually a video file
                        if file.suffix.lower() in [".html", ".mhtml", ".htm"]:
                            logger.error(
                                f"❌ Downloaded HTML instead of video: {file.name}"
                            )
                            # Show first few lines of the file
                            try:
                                with open(
                                    file, "r", encoding="utf-8", errors="ignore"
                                ) as f:
                                    content = f.read(500)
                                    logger.error(
                                        f"File content preview: {content[:200]}..."
                                    )
                            except:
                                pass
                        elif file_size < 1024:
                            logger.warning(f"⚠️ File is very small ({file_size} bytes)")
                        else:
                            logger.info(f"✅ Looks like a valid video file")

                        # Clean up for next test
                        file.unlink()
                else:
                    logger.error(f"❌ No files downloaded for {config['name']}")

            except Exception as e:
                logger.error(f"❌ {config['name']} failed: {e}")


def main():
    """Main diagnostic function"""
    logger.info("=== YouTube-DL Diagnostic Tool ===\n")

    # Test URLs (use the same ones from the logs)
    test_urls = [
        "https://www.youtube.com/watch?v=9sYscsSocPw",
        "https://www.youtube.com/watch?v=ss-m4HFObMg",
    ]

    # Test yt-dlp version and update
    test_ytdlp_version()

    for url in test_urls:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing URL: {url}")
        logger.info(f"{'='*60}")

        # Test info extraction first
        if test_simple_extraction(url):
            logger.info("Info extraction successful, testing download...")
            test_download_with_configs(url)
        else:
            logger.error("Info extraction failed, skipping download test")

    logger.info("\n=== Diagnostic complete ===")


if __name__ == "__main__":
    main()
