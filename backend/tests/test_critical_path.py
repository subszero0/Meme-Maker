"""
Critical Path E2E Test - Phase 2.3 of TestsToDo.md

One test to rule them all - covers 80% of user value.
Real API calls, minimal mocking, complete user journey.
"""

import time

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.e2e
@pytest.mark.skip(
    reason="E2E test requires live backend server and external services - run manually"
)
class TestCompleteUserJourney:
    """
    Complete user journey E2E test.

    This test covers the entire user flow:
    URL → Metadata → Job → Download

    Should complete in < 60 seconds and cover 80% of user value.
    """

    @pytest.fixture
    def client(self):
        """Test client for E2E testing"""
        return TestClient(app)

    def test_complete_user_journey(self, client):
        """
        Test complete user journey from URL paste to download.

        This single test replaces 25+ individual tests by focusing on
        the core business value: can a user clip a video?
        """
        # Step 1: Fetch metadata for a real video
        print("🎬 Step 1: Fetching video metadata...")

        metadata_payload = {
            # Rick Roll - reliable test video
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        }

        metadata_response = client.post("/api/v1/metadata", json=metadata_payload)

        # Assert metadata fetch succeeds
        assert (
            metadata_response.status_code == 200
        ), f"Metadata fetch failed: {metadata_response.text}"

        metadata = metadata_response.json()
        assert "title" in metadata
        assert "duration" in metadata
        assert metadata["duration"] > 0

        print(f"   ✅ Got metadata: {metadata['title']} ({metadata['duration']}s)")

        # Step 2: Create a clip job
        print("🎬 Step 2: Creating clip job...")

        job_payload = {
            "url": metadata_payload["url"],
            "start": 10.0,  # 10 seconds in
            "end": 40.0,  # 30 second clip
            "accepted_terms": True,
        }

        job_response = client.post("/api/v1/jobs", json=job_payload)

        # Assert job creation succeeds
        assert (
            job_response.status_code == 202
        ), f"Job creation failed: {job_response.text}"

        job_data = job_response.json()
        assert "job_id" in job_data
        assert job_data["status"] == "queued"

        job_id = job_data["job_id"]
        print(f"   ✅ Created job: {job_id}")

        # Step 3: Poll job status until completion
        print("🎬 Step 3: Polling job status...")

        max_wait_time = 60  # 60 seconds max wait
        poll_interval = 2  # Poll every 2 seconds
        start_time = time.time()

        final_status = None

        while time.time() - start_time < max_wait_time:
            status_response = client.get(f"/api/v1/jobs/{job_id}")

            # Assert status check succeeds
            assert (
                status_response.status_code == 200
            ), f"Status check failed: {status_response.text}"

            status_data = status_response.json()
            current_status = status_data["status"]
            progress = status_data.get("progress", 0)

            print(f"   📊 Status: {current_status}, Progress: {progress}%")

            if current_status == "done":
                final_status = status_data
                print("   ✅ Job completed successfully!")
                break
            elif current_status == "error":
                error_msg = status_data.get("error_message", "Unknown error")
                pytest.fail(f"Job failed with error: {error_msg}")

            time.sleep(poll_interval)

        # Assert job completed within time limit
        assert (
            final_status is not None
        ), f"Job did not complete within {max_wait_time} seconds"
        assert final_status["status"] == "done"
        assert final_status["progress"] == 100

        # Step 4: Verify download URL is available
        print("🎬 Step 4: Verifying download URL...")

        assert (
            "link" in final_status or "url" in final_status
        ), "No download URL in completed job"

        download_url = final_status.get("link") or final_status.get("url")
        assert download_url is not None
        assert download_url.startswith("http"), f"Invalid download URL: {download_url}"

        print(f"   ✅ Download URL available: {download_url[:50]}...")

        # Step 5: Verify download URL is accessible (optional - depends on S3 setup)
        print("🎬 Step 5: Testing download URL accessibility...")

        # Note: In a real E2E test, you might want to actually download the file
        # For now, we just verify the URL format is correct

        # Basic URL validation
        assert (
            "s3" in download_url.lower()
            or "amazonaws" in download_url.lower()
            or "localhost" in download_url.lower()
        ), f"Download URL doesn't appear to be a valid storage URL: {download_url}"

        print("   ✅ Download URL format is valid")

        # Test Summary
        elapsed_time = time.time() - start_time
        print(f"\n🎉 Complete user journey test PASSED in {elapsed_time:.1f} seconds!")
        print("   📊 Covered: Metadata → Job Creation → Processing → Download")
        print("   🎯 Business Value: User can successfully clip a video end-to-end")


@pytest.mark.e2e
@pytest.mark.skip(reason="E2E test requires live backend server - run manually")
class TestCriticalErrorPaths:
    """
    Test critical error paths that users might encounter.

    These are the most important error scenarios that affect user experience.
    """

    @pytest.fixture
    def client(self):
        """Test client for E2E testing"""
        return TestClient(app)

    def test_invalid_video_url_error_path(self, client):
        """Test that invalid video URLs are handled gracefully"""
        # Arrange
        invalid_payload = {"url": "https://example.com/not-a-video"}

        # Act
        response = client.post("/api/v1/metadata", json=invalid_payload)

        # Assert
        assert response.status_code in [400, 422]
        error_data = response.json()
        assert "detail" in error_data

        print("   ✅ Invalid URL handled gracefully")

    def test_clip_too_long_error_path(self, client):
        """Test that clips over 30 minutes are rejected"""
        # Arrange
        long_clip_payload = {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "start": 0.0,
            "end": 1900.0,  # Over 30 minutes
            "accepted_terms": True,
        }

        # Act
        response = client.post("/api/v1/jobs", json=long_clip_payload)

        # Assert
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data

        print("   ✅ Long clip duration rejected properly")
