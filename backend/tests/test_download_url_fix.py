"""
Test for download URL generation fix
Ensures that BASE_URL is properly used for staging/production environments
"""

from unittest.mock import Mock, patch

from backend.app.storage import LocalStorageManager


class TestDownloadURLFix:
    """Test download URL generation with proper BASE_URL handling"""

    def test_download_url_with_staging_base_url(self):
        """Test that staging BASE_URL is used correctly"""
        # Mock settings with staging BASE_URL
        mock_settings = Mock()
        mock_settings.base_url = "http://13.126.173.223:8001"
        mock_settings.clips_dir = "/app/storage/clips"

        with patch("backend.app.storage.settings", mock_settings):
            storage = LocalStorageManager()

            job_id = "test-job-123"
            filename = "test_video.mp4"

            download_url = storage.get_download_url(job_id, filename)

            # Should return full staging URL, not relative URL
            expected_url = (
                "http://13.126.173.223:8001/api/v1/jobs/test-job-123/download"
            )
            assert download_url == expected_url

    def test_download_url_with_production_base_url(self):
        """Test that production BASE_URL is used correctly"""
        # Mock settings with production BASE_URL
        mock_settings = Mock()
        mock_settings.base_url = "https://memeit.pro"
        mock_settings.clips_dir = "/app/storage/clips"

        with patch("backend.app.storage.settings", mock_settings):
            storage = LocalStorageManager()

            job_id = "test-job-456"
            filename = "test_video.mp4"

            download_url = storage.get_download_url(job_id, filename)

            # Should return full production URL
            expected_url = "https://memeit.pro/api/v1/jobs/test-job-456/download"
            assert download_url == expected_url

    def test_download_url_with_localhost_base_url(self):
        """Test that localhost BASE_URL is used correctly"""
        # Mock settings with localhost BASE_URL
        mock_settings = Mock()
        mock_settings.base_url = "http://localhost:8000"
        mock_settings.clips_dir = "/app/storage/clips"

        with patch("backend.app.storage.settings", mock_settings):
            storage = LocalStorageManager()

            job_id = "test-job-789"
            filename = "test_video.mp4"

            download_url = storage.get_download_url(job_id, filename)

            # Should return full localhost URL
            expected_url = "http://localhost:8000/api/v1/jobs/test-job-789/download"
            assert download_url == expected_url

    def test_download_url_with_empty_base_url(self):
        """Test fallback to relative URL when BASE_URL is empty"""
        # Mock settings with empty BASE_URL
        mock_settings = Mock()
        mock_settings.base_url = ""
        mock_settings.clips_dir = "/app/storage/clips"

        with patch("backend.app.storage.settings", mock_settings):
            storage = LocalStorageManager()

            job_id = "test-job-empty"
            filename = "test_video.mp4"

            download_url = storage.get_download_url(job_id, filename)

            # Should return relative URL as fallback
            expected_url = "/api/v1/jobs/test-job-empty/download"
            assert download_url == expected_url

    def test_download_url_with_none_base_url(self):
        """Test fallback to relative URL when BASE_URL is None"""
        # Mock settings with None BASE_URL
        mock_settings = Mock()
        mock_settings.base_url = None
        mock_settings.clips_dir = "/app/storage/clips"

        with patch("backend.app.storage.settings", mock_settings):
            storage = LocalStorageManager()

            job_id = "test-job-none"
            filename = "test_video.mp4"

            download_url = storage.get_download_url(job_id, filename)

            # Should return relative URL as fallback
            expected_url = "/api/v1/jobs/test-job-none/download"
            assert download_url == expected_url

    def test_download_url_regression_test(self):
        """Regression test: Ensure the old broken logic doesn't return"""
        # This test ensures we don't accidentally revert to the old logic
        # that returned relative URLs for non-localhost BASE_URLs

        mock_settings = Mock()
        mock_settings.base_url = "http://13.126.173.223:8001"  # Staging URL
        mock_settings.clips_dir = "/app/storage/clips"

        with patch("backend.app.storage.settings", mock_settings):
            storage = LocalStorageManager()

            job_id = "regression-test-job"
            filename = "test_video.mp4"

            download_url = storage.get_download_url(job_id, filename)

            # Should NOT be relative URL (old broken behavior)
            assert not download_url.startswith("/api/v1/jobs/")

            # Should be full URL with staging BASE_URL (new correct behavior)
            assert (
                download_url
                == "http://13.126.173.223:8001/api/v1/jobs/regression-test-job/download"
            )

            # Verify it doesn't contain the broken pattern
            assert "http://api/" not in download_url
