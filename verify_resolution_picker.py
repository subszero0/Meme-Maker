#!/usr/bin/env python3
"""
Simple verification script for the resolution picker fix.
Run this after starting Docker to verify different resolutions produce different file sizes.
"""

import requests
import time
import sys

API_BASE_URL = "http://localhost:8000/api/v1"
TEST_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

def test_with_docker():
    """Test resolution picker through the full Docker pipeline"""
    print("🧪 Testing Resolution Picker via Docker Pipeline")
    print("=" * 50)
    
    # Check if backend is running
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend service not responding correctly")
            print("Please start Docker services with: docker-compose up -d")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("Please start Docker services with: docker-compose up -d")
        return False
    
    print("✅ Backend service is running")
    
    # Get available formats
    print(f"📋 Getting available formats for test video...")
    try:
        response = requests.post(f"{API_BASE_URL}/metadata/extract", json={"url": TEST_URL}, timeout=30)
        response.raise_for_status()
        data = response.json()
        formats = data.get('formats', [])
    except Exception as e:
        print(f"❌ Failed to get formats: {e}")
        return False
    
    if not formats:
        print("❌ No formats available")
        return False
    
    # Select 2 different resolutions for testing  
    test_formats = []
    seen_resolutions = set()
    
    for fmt in formats:
        resolution = fmt.get('resolution', 'unknown')
        if resolution not in seen_resolutions and len(test_formats) < 2:
            test_formats.append(fmt)
            seen_resolutions.add(resolution)
    
    if len(test_formats) < 2:
        print("❌ Need at least 2 different resolutions to test")
        return False
    
    print(f"🎯 Testing with formats:")
    for fmt in test_formats:
        print(f"  - {fmt['format_id']}: {fmt['resolution']}")
    
    # Test each format
    results = []
    for fmt in test_formats:
        format_id = fmt['format_id']
        resolution = fmt['resolution']
        
        print(f"\n🔄 Testing {format_id} ({resolution})...")
        
        # Create job
        try:
            response = requests.post(f"{API_BASE_URL}/jobs", json={
                "url": TEST_URL,
                "in_ts": 0.0,
                "out_ts": 10.0,
                "format_id": format_id
            }, timeout=30)
            response.raise_for_status()
            job_id = response.json()['id']
            print(f"  Created job: {job_id}")
        except Exception as e:
            print(f"  ❌ Failed to create job: {e}")
            continue
        
        # Wait for completion
        download_url = None
        for _ in range(24):  # 2 minutes max
            try:
                response = requests.get(f"{API_BASE_URL}/jobs/{job_id}")
                response.raise_for_status()
                data = response.json()
                status = data.get('status')
                
                if status == 'done':
                    download_url = data.get('download_url')
                    print(f"  ✅ Job completed!")
                    break
                elif status == 'error':
                    print(f"  ❌ Job failed: {data.get('error_code')}")
                    break
                else:
                    print(f"  📊 Status: {status} ({data.get('progress', 0)}%)")
                    time.sleep(5)
            except Exception as e:
                print(f"  ❌ Error checking status: {e}")
                break
        
        if download_url:
            # Get file size from download URL
            try:
                response = requests.head(download_url, timeout=10)
                file_size = int(response.headers.get('content-length', 0))
                results.append({
                    'format_id': format_id,
                    'resolution': resolution,
                    'file_size': file_size
                })
                print(f"  📊 File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
            except Exception as e:
                print(f"  ⚠️  Could not get file size: {e}")
        else:
            print(f"  ❌ Job did not complete successfully")
    
    # Analyze results
    print(f"\n📊 Final Results")
    print("=" * 30)
    
    if len(results) < 2:
        print("❌ Not enough successful tests to compare")
        return False
    
    file_sizes = [r['file_size'] for r in results]
    if len(set(file_sizes)) == 1:
        print("🚨 ISSUE: All files have identical sizes!")
        for result in results:
            print(f"  {result['format_id']} ({result['resolution']}): {result['file_size']:,} bytes")
        return False
    else:
        print("✅ SUCCESS: Different formats produced different file sizes!")
        for result in results:
            print(f"  {result['format_id']} ({result['resolution']}): {result['file_size']:,} bytes")
        return True

if __name__ == "__main__":
    success = test_with_docker()
    if success:
        print("\n🎉 Resolution picker is working correctly!")
    else:
        print("\n❌ Resolution picker still needs attention.")
        print("Try restarting Docker services: docker-compose down && docker-compose up -d")
    
    sys.exit(0 if success else 1) 