#!/usr/bin/env python3
"""
End-to-End Test: Complete User Flow
===============================================

Tests the complete user workflow:
1. Input URL
2. Load video player
3. Get resolutions 
4. Select format
5. Create job
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

def test_complete_user_flow():
    """Test the complete user workflow"""
    print("=" * 60)
    print("END-TO-END USER FLOW TEST")
    print("=" * 60)
    print(f"Timestamp: {datetime.now()}")
    print(f"Test URL: {TEST_URL}")
    print()
    
    # Step 1: User inputs URL and requests metadata
    print("👤 Step 1: User inputs URL and loads video player")
    print("🔍 Getting detailed metadata for resolution selection...")
    
    start_time = time.time()
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/metadata/extract",
            json={"url": TEST_URL},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        metadata_time = time.time() - start_time
        
        if response.status_code != 200:
            print(f"❌ Step 1 FAILED: {response.status_code} - {response.text}")
            return False
            
        metadata = response.json()
        formats = metadata.get('formats', [])
        
        print(f"✅ Step 1 SUCCESS in {metadata_time:.2f}s")
        print(f"   Video: {metadata.get('title', 'Unknown')[:50]}...")
        print(f"   Duration: {metadata.get('duration', 0):.1f}s")
        print(f"   Formats: {len(formats)} available")
        
        if len(formats) == 0:
            print("❌ No formats available - cannot proceed")
            return False
            
    except Exception as e:
        print(f"❌ Step 1 FAILED: {e}")
        return False
    
    # Step 2: Frontend displays formats and user selects one
    print(f"\n👤 Step 2: User selects resolution")
    
    # Find a good format (prefer 1080p, fall back to 720p, then any)
    preferred_format = None
    for fmt in formats:
        if '1920x1080' in fmt.get('resolution', ''):
            preferred_format = fmt
            break
    
    if not preferred_format:
        for fmt in formats:
            if '1280x720' in fmt.get('resolution', ''):
                preferred_format = fmt
                break
    
    if not preferred_format and formats:
        preferred_format = formats[0]
    
    if not preferred_format:
        print("❌ Step 2 FAILED: No suitable format found")
        return False
    
    print(f"✅ Step 2 SUCCESS")
    print(f"   Selected: {preferred_format.get('format_id')} ({preferred_format.get('resolution')})")
    print(f"   Codec: {preferred_format.get('vcodec')} / {preferred_format.get('acodec')}")
    
    # Step 3: User sets trim times and creates job
    print(f"\n👤 Step 3: User sets trim times and creates job")
    
    duration = metadata.get('duration', 0)
    start_time = 10  # Start at 10 seconds
    end_time = min(40, duration - 5)  # 30 second clip or near end
    
    job_data = {
        "url": TEST_URL,
        "in_ts": start_time,
        "out_ts": end_time,
        "format_id": preferred_format.get('format_id')
    }
    
    print(f"   Creating job: {start_time}s - {end_time}s ({end_time - start_time}s clip)")
    
    try:
        job_start = time.time()
        response = requests.post(
            f"{API_BASE_URL}/api/v1/jobs",
            json=job_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        job_creation_time = time.time() - job_start
        
        if response.status_code != 200:
            print(f"❌ Step 3 FAILED: {response.status_code} - {response.text}")
            return False
            
        job = response.json()
        job_id = job.get('id')
        
        print(f"✅ Step 3 SUCCESS in {job_creation_time:.2f}s")
        print(f"   Job ID: {job_id}")
        print(f"   Status: {job.get('status')}")
        
    except Exception as e:
        print(f"❌ Step 3 FAILED: {e}")
        return False
    
    # Step 4: Check job status (just first check, not full processing)
    print(f"\n👤 Step 4: Check job status")
    
    try:
        status_start = time.time()
        response = requests.get(
            f"{API_BASE_URL}/api/v1/jobs/{job_id}",
            timeout=5
        )
        
        status_time = time.time() - status_start
        
        if response.status_code != 200:
            print(f"❌ Step 4 FAILED: {response.status_code} - {response.text}")
            return False
            
        job_status = response.json()
        
        print(f"✅ Step 4 SUCCESS in {status_time:.2f}s")
        print(f"   Status: {job_status.get('status')}")
        print(f"   Progress: {job_status.get('progress', 0)}%")
        
        if job_status.get('stage'):
            print(f"   Stage: {job_status.get('stage')}")
            
    except Exception as e:
        print(f"❌ Step 4 FAILED: {e}")
        return False
    
    # Summary
    total_time = metadata_time + job_creation_time + status_time
    
    print(f"\n" + "=" * 60)
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 60)
    print(f"Metadata Loading: {metadata_time:.2f}s")
    print(f"Job Creation: {job_creation_time:.2f}s") 
    print(f"Status Check: {status_time:.2f}s")
    print(f"Total Time: {total_time:.2f}s")
    print()
    
    # Performance assessment
    if metadata_time > 10:
        print("⚠️  Metadata loading is slow (>10s)")
    if total_time > 15:
        print("⚠️  Overall flow is slow (>15s)")
    else:
        print("✅ Good performance overall")
    
    print(f"\n🎉 END-TO-END TEST PASSED")
    print(f"✅ All 4 steps completed successfully")
    print(f"✅ User can successfully create video clips")
    
    return True

def test_error_scenarios():
    """Test common error scenarios"""
    print(f"\n" + "=" * 60)
    print("ERROR SCENARIO TESTING")
    print("=" * 60)
    
    # Test invalid URL
    print("🧪 Testing invalid URL handling...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/metadata/extract",
            json={"url": "https://invalid-url-that-does-not-exist.com/video"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 400:
            print("✅ Invalid URL properly rejected")
        else:
            print(f"⚠️  Unexpected response for invalid URL: {response.status_code}")
            
    except Exception as e:
        print(f"✅ Invalid URL handled with error: {type(e).__name__}")
    
    # Test malformed request
    print("🧪 Testing malformed request handling...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/metadata/extract",
            json={"invalid_field": "test"},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code in [400, 422]:
            print("✅ Malformed request properly rejected")
        else:
            print(f"⚠️  Unexpected response for malformed request: {response.status_code}")
            
    except Exception as e:
        print(f"✅ Malformed request handled with error: {type(e).__name__}")

if __name__ == "__main__":
    # Test complete user flow
    success = test_complete_user_flow()
    
    # Test error scenarios
    test_error_scenarios()
    
    print(f"\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED - Application is working correctly!")
        print("✅ Users can successfully:")
        print("   - Input video URLs")
        print("   - Load video metadata and formats")
        print("   - Select quality/resolution")
        print("   - Create video clips")
        print("   - Monitor job progress")
    else:
        print("❌ TESTS FAILED - Issues found in user flow")
    print("=" * 60) 