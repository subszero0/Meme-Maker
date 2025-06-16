#!/usr/bin/env python3
"""
Resolution Comparison Test
Tests multiple resolutions to verify different file sizes are produced.
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"
TEST_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

def get_available_formats():
    """Get available formats for the test video"""
    print("🔍 Getting available formats...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/metadata/extract", 
                               json={"url": TEST_URL}, 
                               timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Metadata extraction failed: {response.status_code}")
            return []
        
        data = response.json()
        formats = data.get('formats', [])
        
        print(f"✅ Found {len(formats)} formats:")
        for i, fmt in enumerate(formats):
            print(f"  {i+1}. {fmt['format_id']} - {fmt['resolution']} ({fmt.get('filesize', 'unknown size')})")
        
        return formats
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def test_resolution(format_id, resolution_name, test_number):
    """Test a specific resolution and return file size"""
    print(f"\n🎬 Test #{test_number}: Testing {resolution_name} (format_id: {format_id})")
    
    # Create job
    job_data = {
        "url": TEST_URL,
        "in_ts": 10.0,
        "out_ts": 15.0,  # 5-second clip for faster testing
        "format_id": format_id
    }
    
    try:
        # Create job
        response = requests.post(f"{BASE_URL}/api/v1/jobs", json=job_data, timeout=30)
        if response.status_code != 201:
            print(f"❌ Job creation failed: {response.status_code}")
            return None
        
        job_id = response.json()['id']
        print(f"✅ Job created: {job_id}")
        
        # Wait for completion
        max_wait = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_response = requests.get(f"{BASE_URL}/api/v1/jobs/{job_id}", timeout=10)
            if status_response.status_code != 200:
                print(f"❌ Status check failed")
                return None
            
            job_status = status_response.json()
            status = job_status['status']
            progress = job_status.get('progress', 0)
            
            if status == 'done':
                download_url = job_status.get('download_url')
                if download_url:
                    # Get file size from download URL
                    head_response = requests.head(download_url, timeout=10)
                    if head_response.status_code == 200:
                        file_size = int(head_response.headers.get('content-length', 0))
                        file_size_mb = file_size / (1024 * 1024)
                        print(f"✅ {resolution_name}: {file_size:,} bytes ({file_size_mb:.2f} MB)")
                        return file_size
                    else:
                        print(f"❌ Could not get file size for {resolution_name}")
                        return None
                else:
                    print(f"❌ No download URL for {resolution_name}")
                    return None
            elif status == 'error':
                print(f"❌ Job failed for {resolution_name}")
                return None
            
            time.sleep(3)  # Check every 3 seconds
        
        print(f"⏰ Timeout waiting for {resolution_name}")
        return None
        
    except Exception as e:
        print(f"❌ Error testing {resolution_name}: {e}")
        return None

def main():
    print("🧪 Resolution File Size Comparison Test")
    print("=" * 60)
    
    # Check backend
    try:
        requests.get(f"{BASE_URL}/health", timeout=5)
        print("✅ Backend is running")
    except:
        print("❌ Backend not running!")
        return 1
    
    # Get available formats
    formats = get_available_formats()
    if not formats:
        print("❌ No formats available")
        return 1
    
    # Select 3-4 different resolutions for testing
    test_formats = []
    
    # Try to get a variety of resolutions
    for fmt in formats:
        resolution = fmt['resolution']
        if any(res in resolution for res in ['2160', '1080', '720', '480']):  # 4K, 1080p, 720p, 480p
            test_formats.append((fmt['format_id'], resolution))
            if len(test_formats) >= 4:  # Test max 4 formats
                break
    
    if len(test_formats) < 2:
        print("❌ Need at least 2 different resolutions to compare")
        return 1
    
    print(f"\n🎯 Testing {len(test_formats)} resolutions for file size differences...")
    print("Each test creates a 5-second clip for comparison.")
    
    results = []
    
    for i, (format_id, resolution) in enumerate(test_formats):
        file_size = test_resolution(format_id, resolution, i + 1)
        if file_size:
            results.append((resolution, file_size, format_id))
        
        # Small delay between tests
        if i < len(test_formats) - 1:
            print("⏳ Waiting 10 seconds before next test...")
            time.sleep(10)
    
    # Analysis
    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY")
    print("=" * 60)
    
    if len(results) < 2:
        print("❌ Not enough successful tests to compare")
        return 1
    
    # Sort by file size (descending)
    results.sort(key=lambda x: x[1], reverse=True)
    
    print("File sizes by resolution:")
    for i, (resolution, file_size, format_id) in enumerate(results):
        file_size_mb = file_size / (1024 * 1024)
        print(f"  {i+1}. {resolution} (ID: {format_id}): {file_size:,} bytes ({file_size_mb:.2f} MB)")
    
    # Check if there are meaningful differences
    largest = results[0][1]
    smallest = results[-1][1]
    difference_ratio = largest / smallest if smallest > 0 else 0
    
    print(f"\n📈 File size ratio (largest/smallest): {difference_ratio:.2f}x")
    
    if difference_ratio > 1.5:  # At least 50% difference
        print("✅ SUCCESS: Resolution picker is working! Different resolutions produce different file sizes.")
        print(f"✅ Higher resolution videos are significantly larger ({difference_ratio:.1f}x difference)")
        return 0
    else:
        print("⚠️  WARNING: File sizes are too similar. Resolution picker may not be working properly.")
        print("💡 This could mean all videos are being processed at the same resolution.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 