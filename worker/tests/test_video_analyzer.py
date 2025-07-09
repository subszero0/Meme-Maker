"""
Unit tests for VideoAnalyzer
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add worker directory to path for imports
worker_dir = Path(__file__).parent.parent
sys.path.insert(0, str(worker_dir))


class TestVideoAnalyzer:
    """Test VideoAnalyzer functionality with mocked dependencies"""

    def test_sanitize_filename_basic(self):
        """Test basic filename sanitization"""
        from video.analyzer import VideoAnalyzer

        # Mock progress tracker
        mock_tracker = Mock()
        analyzer = VideoAnalyzer(mock_tracker)

        # Test cases
        test_cases = [
            ("Hello World", "Hello_World"),
            ("My Video Title.mp4", "My_Video_Title.mp4"),
            ('Special<>:"/\\|?*Chars', "Special___________Chars"),
            ("Multiple   Spaces", "Multiple_Spaces"),
            ("___Leading_and_Trailing___", "Leading_and_Trailing"),
            ("", "video"),
            ("   ", "video"),
            ("A" * 150, "A" * 100),  # Test max length truncation
        ]

        for input_title, expected in test_cases:
            result = analyzer.sanitize_filename(input_title)
            assert result == expected, f"Failed for input: '{input_title}'"

    def test_sanitize_filename_unicode_and_special_chars(self):
        """Test filename sanitization with unicode and special characters"""
        from video.analyzer import VideoAnalyzer

        mock_tracker = Mock()
        analyzer = VideoAnalyzer(mock_tracker)

        # Test unicode characters get removed
        result = analyzer.sanitize_filename("Hello 世界 Wörld")
        assert result == "Hello_Wrld"  # Unicode chars removed

        # Test parentheses and brackets are kept
        result = analyzer.sanitize_filename("Video (2023) [HD]")
        assert result == "Video_(2023)_[HD]"

        # Test dots are kept
        result = analyzer.sanitize_filename("video.part1.mp4")
        assert result == "video.part1.mp4"

    def test_sanitize_filename_max_length(self):
        """Test filename sanitization respects max length"""
        from video.analyzer import VideoAnalyzer

        mock_tracker = Mock()
        analyzer = VideoAnalyzer(mock_tracker)

        # Test custom max length
        long_title = "A" * 200
        result = analyzer.sanitize_filename(long_title, max_length=50)
        assert len(result) == 50
        assert result == "A" * 50

        # Test that it doesn't end with underscore after truncation
        long_title_with_underscore = "A" * 45 + "_____" + "B" * 50
        result = analyzer.sanitize_filename(long_title_with_underscore, max_length=50)
        assert len(result) <= 50
        assert not result.endswith("_")

    @patch("video.analyzer.yt_dlp.YoutubeDL")
    def test_extract_video_title_success(self, mock_youtubedl):
        """Test successful video title extraction"""
        from video.analyzer import VideoAnalyzer

        # Mock progress tracker
        mock_tracker = Mock()
        analyzer = VideoAnalyzer(mock_tracker)

        # Mock yt-dlp response
        mock_ydl_instance = Mock()
        mock_youtubedl.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {"title": "Amazing Video Title!"}

        result = analyzer.extract_video_title("https://example.com/video")

        # Verify yt-dlp was called correctly
        mock_ydl_instance.extract_info.assert_called_once_with(
            "https://example.com/video", download=False
        )

        # Verify title was sanitized
        assert result == "Amazing_Video_Title"

        # Verify progress was updated
        mock_tracker.update.assert_called_once_with(
            2, stage="Extracting video title..."
        )

    @patch("video.analyzer.yt_dlp.YoutubeDL")
    def test_extract_video_title_playlist(self, mock_youtubedl):
        """Test video title extraction from playlist"""
        from video.analyzer import VideoAnalyzer

        mock_tracker = Mock()
        analyzer = VideoAnalyzer(mock_tracker)

        # Mock yt-dlp response for playlist
        mock_ydl_instance = Mock()
        mock_youtubedl.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {
            "entries": [
                {"title": "First Video in Playlist"},
                {"title": "Second Video in Playlist"},
            ]
        }

        result = analyzer.extract_video_title("https://example.com/playlist")

        # Should get the first video's title
        assert result == "First_Video_in_Playlist"

    @patch("video.analyzer.yt_dlp.YoutubeDL")
    def test_extract_video_title_empty_title(self, mock_youtubedl):
        """Test handling of empty or missing title"""
        from video.analyzer import VideoAnalyzer

        mock_tracker = Mock()
        analyzer = VideoAnalyzer(mock_tracker)

        # Mock yt-dlp response with empty title
        mock_ydl_instance = Mock()
        mock_youtubedl.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {"title": ""}

        result = analyzer.extract_video_title("https://example.com/video")
        assert result == "video"

        # Test missing title key
        mock_ydl_instance.extract_info.return_value = {}
        result = analyzer.extract_video_title("https://example.com/video")
        assert result == "video"

    @patch("video.analyzer.yt_dlp.YoutubeDL")
    @patch("video.analyzer.logger")
    def test_extract_video_title_exception(self, mock_logger, mock_youtubedl):
        """Test handling of yt-dlp exceptions"""
        from video.analyzer import VideoAnalyzer

        mock_tracker = Mock()
        analyzer = VideoAnalyzer(mock_tracker)

        # Mock yt-dlp to raise exception
        mock_ydl_instance = Mock()
        mock_youtubedl.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.side_effect = Exception("Network error")

        result = analyzer.extract_video_title("https://example.com/video")

        # Should return default and log warning
        assert result == "video"
        mock_logger.warning.assert_called_once()
        warning_msg = mock_logger.warning.call_args[0][0]
        assert "Failed to extract title" in warning_msg

    @patch("video.analyzer.subprocess.run")
    @patch("video.analyzer.json.loads")
    def test_analyze_video_file_success(self, mock_json_loads, mock_subprocess):
        """Test successful video file analysis"""
        from video.analyzer import VideoAnalyzer
        from video.analyzer import VideoAnalysisError

        mock_tracker = Mock()
        analyzer = VideoAnalyzer(mock_tracker)

        # Mock subprocess response
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = '{"streams": [], "format": {}}'

        # Mock JSON parsing
        mock_json_loads.return_value = {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080,
                    "avg_frame_rate": "30/1",
                    "pix_fmt": "yuv420p",
                    "duration": "120.5",
                },
                {"codec_type": "audio", "codec_name": "aac", "sample_rate": "44100"},
            ],
            "format": {"duration": "120.5"},
        }

        # Create a mock file path
        test_file = Path("/tmp/test_video.mp4")

        # Mock file stats
        with patch.object(test_file, "stat") as mock_stat:
            mock_stat.return_value.st_size = 50000000  # 50MB

            # This would be async in real implementation, but testing sync version
            import asyncio

            result = asyncio.run(analyzer.analyze_video_file(test_file))

        # Verify results
        assert result["video_streams"] == 1
        assert result["audio_streams"] == 1
        assert result["video_codec"] == "h264"
        assert result["width"] == 1920
        assert result["height"] == 1080
        assert result["audio_codec"] == "aac"
        assert result["file_size"] == 50000000

        # Verify progress was updated
        mock_tracker.update.assert_called_once_with(25, stage="Analyzing video...")

    @patch("video.analyzer.subprocess.run")
    def test_analyze_video_file_no_video_streams(self, mock_subprocess):
        """Test analysis failure when no video streams found"""
        from video.analyzer import VideoAnalyzer, VideoAnalysisError

        mock_tracker = Mock()
        analyzer = VideoAnalyzer(mock_tracker)

        # Mock subprocess response with no video streams
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = '{"streams": [], "format": {}}'

        test_file = Path("/tmp/test_video.mp4")

        with patch.object(test_file, "stat") as mock_stat:
            mock_stat.return_value.st_size = 1000

            # Should raise VideoAnalysisError
            with pytest.raises(VideoAnalysisError) as exc_info:
                import asyncio

                asyncio.run(analyzer.analyze_video_file(test_file))

            assert "No video streams found" in str(exc_info.value)
            assert exc_info.value.job_id == mock_tracker.job_id

    @patch("video.analyzer.subprocess.run")
    def test_analyze_video_file_subprocess_error(self, mock_subprocess):
        """Test analysis failure when subprocess fails"""
        from video.analyzer import VideoAnalyzer, VideoAnalysisError
        import subprocess

        mock_tracker = Mock()
        analyzer = VideoAnalyzer(mock_tracker)

        # Mock subprocess to raise CalledProcessError
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "ffprobe")

        test_file = Path("/tmp/test_video.mp4")

        # Should raise VideoAnalysisError
        with pytest.raises(VideoAnalysisError) as exc_info:
            import asyncio

            asyncio.run(analyzer.analyze_video_file(test_file))

        assert "Cannot analyze video file" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__])
