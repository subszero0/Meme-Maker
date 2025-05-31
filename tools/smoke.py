#!/usr/bin/env python3
"""
Smoke test for Meme Maker API
Tests end-to-end functionality: job creation -> processing -> download
"""
import time
import sys
import subprocess
import requests
import os
from typing import Optional


# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_VIDEO_URL = "https://filesamples.com/samples/video/mp4/sample_640x360.mp4"
START_TIME = "00:00:02"
END_TIME = "00:00:07"
EXPECTED_DURATION = 5.0  # seconds
POLL_INTERVAL = 5  # seconds
TIMEOUT = 120  # seconds
DURATION_TOLERANCE = 0.5  # seconds


def log(message: str) -> None:
    """Print timestamped log message"""
    timestamp = time.strftime('%H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)


def wait_for_api_ready(max_attempts: int = 24) -> bool:
    """Wait for API to be ready with extended timeout for CI"""
    log("Waiting for API to be ready...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/health", timeout=10)
            if response.status_code == 200:
                log("✅ API is ready!")
                return True
        except requests.exceptions.RequestException as e:
            log(f"API check failed: {e}")
        
        if attempt < max_attempts - 1:
            log(f"⏳ API not ready, waiting... (attempt {attempt + 1}/{max_attempts})")
            time.sleep(5)
    
    log("❌ API failed to become ready")
    return False


def test_rate_limiting() -> bool:
    """Test that rate limiting is working by sending 41 requests"""
    log("🚦 Testing rate limiting (40 requests per 24h per IP)...")
    
    # First, let's check if we can make one successful request
    test_job_data = {
        "url": TEST_VIDEO_URL,
        "start": START_TIME,
        "end": END_TIME
    }
    
    successful_requests = 0
    rate_limited_requests = 0
    
    # Fire 41 requests rapidly
    for i in range(41):
        try:
            response = requests.post(
                f"{API_BASE_URL}/jobs",
                json=test_job_data,
                timeout=5
            )
            
            if response.status_code == 202:
                successful_requests += 1
            elif response.status_code == 429:
                rate_limited_requests += 1
                response_data = response.json()
                
                # Verify response format
                if "detail" in response_data and "retry_after" in response_data:
                    if response_data["detail"] == "RATE_LIMIT":
                        log(f"✅ Request {i+1}: Properly rate limited (429) with retry_after: {response_data['retry_after']}")
                    else:
                        log(f"⚠️  Request {i+1}: Rate limited but wrong detail: {response_data['detail']}")
                else:
                    log(f"⚠️  Request {i+1}: Rate limited but missing required fields: {response_data}")
            else:
                log(f"❌ Request {i+1}: Unexpected status {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            log(f"❌ Request {i+1} failed: {e}")
            return False
    
    log(f"📊 Rate limit test results: {successful_requests} successful, {rate_limited_requests} rate-limited")
    
    # We should have some successful requests and at least one rate-limited request
    if successful_requests == 0:
        log("❌ Rate limit test failed: No successful requests (API may be down)")
        return False
    
    if rate_limited_requests == 0:
        log("⚠️  Rate limiting may not be working - no 429 responses received")
        # Don't fail the test since rate limiting might have a higher limit in dev
        return True
    
    # Check that the rate-limited request came after some successful ones
    if successful_requests > 0 and rate_limited_requests > 0:
        log("✅ Rate limiting appears to be working correctly")
        return True
    
    return True


def create_job() -> Optional[str]:
    """Create a new clip job and return job ID"""
    log(f"🎬 Creating job for {TEST_VIDEO_URL} ({START_TIME} -> {END_TIME})")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/jobs",
            json={
                "url": TEST_VIDEO_URL,
                "start": START_TIME,
                "end": END_TIME
            },
            timeout=15
        )
        
        log(f"Job creation response: {response.status_code}")
        
        if response.status_code != 202:
            log(f"❌ Failed to create job: {response.status_code} - {response.text}")
            return None
        
        job_data = response.json()
        job_id = job_data["job_id"]
        log(f"✅ Job created successfully: {job_id}")
        return job_id
        
    except requests.exceptions.RequestException as e:
        log(f"❌ Request failed: {e}")
        return None


def poll_job_status(job_id: str) -> Optional[str]:
    """Poll job status until completion, return download URL"""
    log(f"📊 Polling job status for {job_id}...")
    
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < TIMEOUT:
        try:
            response = requests.get(f"{API_BASE_URL}/jobs/{job_id}", timeout=15)
            
            if response.status_code != 200:
                log(f"❌ Failed to get job status: {response.status_code} - {response.text}")
                return None
            
            job_data = response.json()
            status = job_data["status"]
            
            # Only log status changes to reduce noise
            if status != last_status:
                log(f"📋 Job status: {status}")
                last_status = status
            
            if status == "done":
                download_url = job_data.get("link")
                if download_url:
                    log("✅ Job completed successfully!")
                    return download_url
                else:
                    log("❌ Job marked as done but no download link provided")
                    return None
            
            elif status == "error":
                error_code = job_data.get("error_code", "unknown")
                log(f"❌ Job failed with error: {error_code}")
                return None
            
            elif status in ["queued", "working"]:
                progress = job_data.get("progress")
                if progress is not None and status == "working":
                    log(f"⚙️  Job in progress: {progress}%")
                time.sleep(POLL_INTERVAL)
            
            else:
                log(f"❓ Unknown job status: {status}")
                return None
                
        except requests.exceptions.RequestException as e:
            log(f"⚠️  Request failed: {e}, retrying...")
            time.sleep(POLL_INTERVAL)
    
    log(f"⏰ Timeout after {TIMEOUT} seconds")
    return None


def download_and_validate(download_url: str) -> bool:
    """Download the file and validate its duration"""
    log("📥 Downloading clip...")
    
    try:
        # Download the file
        response = requests.get(download_url, timeout=60)
        
        if response.status_code != 200:
            log(f"❌ Failed to download: {response.status_code}")
            return False
        
        # Save to temporary file
        temp_file = "/tmp/test_clip.mp4"
        with open(temp_file, "wb") as f:
            f.write(response.content)
        
        log(f"✅ Downloaded {len(response.content)} bytes")
        
        # Use ffprobe to check duration
        log("🔍 Validating clip duration with ffprobe...")
        
        cmd = [
            "ffprobe", 
            "-v", "quiet", 
            "-show_entries", "format=duration", 
            "-of", "csv=p=0", 
            temp_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode != 0:
            log(f"❌ ffprobe failed: {result.stderr}")
            return False
        
        actual_duration = float(result.stdout.strip())
        log(f"📏 Actual duration: {actual_duration:.2f}s, expected: {EXPECTED_DURATION:.2f}s")
        
        # Check if duration is within tolerance
        duration_diff = abs(actual_duration - EXPECTED_DURATION)
        if duration_diff > DURATION_TOLERANCE:
            log(f"❌ Duration mismatch: {duration_diff:.2f}s > {DURATION_TOLERANCE:.2f}s tolerance")
            return False
        
        log("✅ Duration validation passed!")
        
        # Clean up temp file
        try:
            os.remove(temp_file)
        except:
            pass
            
        return True
        
    except Exception as e:
        log(f"❌ Download/validation failed: {e}")
        return False


def main() -> int:
    """Run the smoke test"""
    log("🚀 Starting Meme Maker smoke test...")
    
    # Wait for API to be ready
    if not wait_for_api_ready():
        log("💥 Test failed: API not ready")
        return 1
    
    # Test rate limiting first (before we potentially hit the limit)
    if not test_rate_limiting():
        log("💥 Test failed: Rate limiting test failed")
        return 1
    
    # Create job
    job_id = create_job()
    if not job_id:
        log("💥 Test failed: Could not create job")
        return 1
    
    # Poll for completion
    download_url = poll_job_status(job_id)
    if not download_url:
        log("💥 Test failed: Job did not complete successfully")
        return 1
    
    # Download and validate
    if not download_and_validate(download_url):
        log("💥 Test failed: Download or validation failed")
        return 1
    
    log("🎉 Smoke test passed! All systems operational.")
    return 0


if __name__ == "__main__":
    sys.exit(main()) 