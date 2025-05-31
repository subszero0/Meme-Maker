"""
End-to-End Smoke Tests for Meme Maker

Tests the complete user flow:
1. Metadata fetch → Job creation → Job completion → Clip download

Environment:
- BASE_URL: API base URL (default: http://localhost:8000)
- TEST_VIDEO_URL: Test video URL (default: yt-dlp test video)
- SKIP_E2E: Skip E2E tests if set to true/1/yes
"""

import time
import tempfile
from pathlib import Path

import pytest
import requests


@pytest.fixture
def session() -> requests.Session:
    """Create a requests session with appropriate timeout"""
    session = requests.Session()
    session.timeout = 30  # 30 second timeout for all requests
    return session


@pytest.mark.e2e
@pytest.mark.smoke
class TestE2EUserFlow:
    """End-to-end tests for the complete user flow"""

    @pytest.mark.slow
    def test_complete_user_flow(self, e2e_config: dict, session: requests.Session, skip_e2e):
        """
        Test the complete user flow from metadata to download
        
        Steps:
        1. Fetch metadata
        2. Create clip job
        3. Poll until completion
        4. Download clip file
        """
        base_url = e2e_config["base_url"]
        test_video_url = e2e_config["test_video_url"]
        
        print(f"\n🔍 Testing E2E flow with URL: {test_video_url}")
        print(f"📡 API Base URL: {base_url}")
        
        # Step 1: Fetch metadata
        print("\n1️⃣ Fetching video metadata...")
        metadata_response = self._fetch_metadata(session, base_url, test_video_url)
        assert metadata_response["duration"] > 0, "Video should have non-zero duration"
        print(f"   ✅ Duration: {metadata_response['duration']} seconds")
        print(f"   ✅ Title: {metadata_response.get('title', 'N/A')}")
        
        # Step 2: Create clip job (first 10 seconds)
        print("\n2️⃣ Creating clip job...")
        job_response = self._create_job(session, base_url, test_video_url)
        job_id = job_response["job_id"]
        assert job_response["status"] == "queued", "Job should start in queued status"
        print(f"   ✅ Job created: {job_id}")
        
        # Step 3: Poll for completion
        print("\n3️⃣ Polling for job completion...")
        final_status = self._poll_until_complete(session, base_url, job_id, e2e_config)
        assert final_status["status"] == "done", f"Job should complete successfully, got: {final_status.get('status')}"
        assert "link" in final_status, "Completed job should have download link"
        print(f"   ✅ Job completed successfully")
        print(f"   ✅ Download link: {final_status['link'][:50]}...")
        
        # Step 4: Download clip
        print("\n4️⃣ Downloading clip file...")
        file_size = self._download_clip(session, final_status["link"], e2e_config["min_clip_size"])
        assert file_size >= e2e_config["min_clip_size"], f"Downloaded file should be at least {e2e_config['min_clip_size']} bytes, got {file_size}"
        print(f"   ✅ Downloaded clip: {file_size:,} bytes")
        
        print("\n🎉 Complete E2E flow successful!")

    @pytest.mark.smoke
    def test_metadata_endpoint_only(self, e2e_config: dict, session: requests.Session):
        """Test metadata endpoint in isolation"""
        base_url = e2e_config["base_url"]
        test_video_url = e2e_config["test_video_url"]
        
        print(f"\n🔍 Testing metadata endpoint with: {test_video_url}")
        
        metadata = self._fetch_metadata(session, base_url, test_video_url)
        
        # Validate metadata structure
        assert "duration" in metadata, "Metadata should include duration"
        assert "title" in metadata, "Metadata should include title"
        assert isinstance(metadata["duration"], (int, float)), "Duration should be numeric"
        assert metadata["duration"] > 0, "Duration should be positive"
        
        print(f"   ✅ Valid metadata: {metadata['duration']}s - {metadata['title']}")

    @pytest.mark.smoke
    def test_job_creation_validation(self, e2e_config: dict, session: requests.Session):
        """Test job creation with various validation scenarios"""
        base_url = e2e_config["base_url"]
        test_video_url = e2e_config["test_video_url"]
        
        print(f"\n🔍 Testing job creation validation")
        
        # Test valid job creation
        job_data = {
            "url": test_video_url,
            "start": "00:00:00",
            "end": "00:00:05"
        }
        
        response = session.post(f"{base_url}/api/v1/jobs", json=job_data)
        assert response.status_code == 202, f"Valid job should return 202, got {response.status_code}"
        
        job_response = response.json()
        assert "job_id" in job_response
        assert job_response["status"] == "queued"
        print(f"   ✅ Valid job created: {job_response['job_id']}")
        
        # Test duration too long (> 3 minutes)
        long_job_data = {
            "url": test_video_url,
            "start": "00:00:00",
            "end": "00:04:00"  # 4 minutes
        }
        
        response = session.post(f"{base_url}/api/v1/jobs", json=long_job_data)
        assert response.status_code == 422, "Job over 3 minutes should be rejected"
        print(f"   ✅ Long duration properly rejected")
        
        # Test invalid time range (end before start)
        invalid_job_data = {
            "url": test_video_url,
            "start": "00:01:00",
            "end": "00:00:30"
        }
        
        response = session.post(f"{base_url}/api/v1/jobs", json=invalid_job_data)
        assert response.status_code == 422, "Invalid time range should be rejected"
        print(f"   ✅ Invalid time range properly rejected")

    def _fetch_metadata(self, session: requests.Session, base_url: str, video_url: str) -> dict:
        """Fetch video metadata"""
        response = session.post(
            f"{base_url}/api/v1/metadata",
            json={"url": video_url}
        )
        
        if response.status_code != 200:
            print(f"❌ Metadata request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
        assert response.status_code == 200, f"Metadata request failed with {response.status_code}: {response.text}"
        return response.json()

    def _create_job(self, session: requests.Session, base_url: str, video_url: str) -> dict:
        """Create a clip job for the first 10 seconds"""
        job_data = {
            "url": video_url,
            "start": "00:00:00",
            "end": "00:00:10"
        }
        
        response = session.post(f"{base_url}/api/v1/jobs", json=job_data)
        
        if response.status_code != 202:
            print(f"❌ Job creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
        assert response.status_code == 202, f"Job creation failed with {response.status_code}: {response.text}"
        return response.json()

    def _poll_until_complete(self, session: requests.Session, base_url: str, job_id: str, config: dict) -> dict:
        """Poll job status until completion or timeout"""
        start_time = time.time()
        last_status = None
        max_wait = config["max_wait_timeout"]
        poll_interval = config["poll_interval"]
        
        while time.time() - start_time < max_wait:
            response = session.get(f"{base_url}/api/v1/jobs/{job_id}")
            
            if response.status_code != 200:
                print(f"❌ Job polling failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
            assert response.status_code == 200, f"Job polling failed with {response.status_code}: {response.text}"
            
            status = response.json()
            current_status = status["status"]
            
            # Log status changes
            if current_status != last_status:
                elapsed = time.time() - start_time
                print(f"   📋 Status: {current_status} (after {elapsed:.1f}s)")
                if "progress" in status and status["progress"] is not None:
                    print(f"   📊 Progress: {status['progress']}%")
                last_status = current_status
            
            # Check for completion states
            if current_status == "done":
                return status
            elif current_status == "error":
                error_code = status.get("error_code", "UNKNOWN")
                pytest.fail(f"Job failed with error: {error_code}")
            
            # Wait before next poll
            time.sleep(poll_interval)
        
        pytest.fail(f"Job {job_id} did not complete within {max_wait} seconds. Last status: {last_status}")

    def _download_clip(self, session: requests.Session, download_url: str, min_size: int) -> int:
        """Download clip file and return size in bytes"""
        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            # Stream download to handle large files
            with session.get(download_url, stream=True) as response:
                if response.status_code != 200:
                    print(f"❌ Download failed: {response.status_code}")
                    print(f"   Response: {response.text}")
                    
                assert response.status_code == 200, f"Download failed with {response.status_code}"
                
                # Write content to temp file
                total_size = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                        total_size += len(chunk)
                
                temp_file.flush()
                
                # Verify file was written
                file_size = Path(temp_file.name).stat().st_size
                assert file_size == total_size, "File size mismatch during download"
                
                return file_size


@pytest.mark.smoke
class TestHealthCheck:
    """Basic health check test"""
    
    def test_health_endpoint(self, e2e_config: dict, session: requests.Session):
        """Test that the health endpoint returns 200"""
        base_url = e2e_config["base_url"]
        response = session.get(f"{base_url}/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        print(f"   ✅ Health check passed")


@pytest.mark.smoke  
class TestAPIAvailability:
    """Test basic API availability before running full E2E tests"""
    
    def test_api_endpoints_reachable(self, e2e_config: dict, session: requests.Session):
        """Test that all required API endpoints are reachable"""
        base_url = e2e_config["base_url"]
        
        # Test health endpoint
        response = session.get(f"{base_url}/health")
        assert response.status_code == 200, f"Health endpoint not reachable: {response.status_code}"
        
        # Test docs endpoint (should exist for FastAPI)
        response = session.get(f"{base_url}/docs")
        assert response.status_code == 200, f"Docs endpoint not reachable: {response.status_code}"
        
        print(f"   ✅ All API endpoints reachable")


if __name__ == "__main__":
    # Allow running tests directly with python -m pytest
    pytest.main([__file__, "-v"]) 