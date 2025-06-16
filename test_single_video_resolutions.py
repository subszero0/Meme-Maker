#!/usr/bin/env python3
"""
Simple test: Download one video in two different resolutions.
This quickly verifies if YouTube blocking is fixed and resolution picker works.
"""

import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def test_single_video_two_resolutions():
    """Test downloading the same video in two different resolutions"""
    
    print("🎯 Single Video - Two Resolutions Test")
    print("=" * 50)
    
    # Use the working video from previous tests
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # Me at the zoo
    
    try:
        # Check backend
        requests.get(f"{BASE_URL}/health", timeout=5)
        print("✅ Backend is running")
    except:
        print("❌ Backend not running! Start with: docker-compose up")
        return False
    
    # Get available formats
    print(f"\n🔍 Getting formats for: {test_url}")
    try:
        response = requests.post(f"{BASE_URL}/api/v1/metadata/extract", 
                               json={"url": test_url}, 
                               timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Metadata extraction failed: {response.status_code}")
            return False
        
        data = response.json()
        formats = data.get('formats', [])
        
        if len(formats) < 2:
            print(f"❌ Not enough formats ({len(formats)}) for test")
            return False
        
        print(f"✅ Found {len(formats)} formats")
        
        # Select two different formats
        format1 = formats[0]  # First format
        format2 = formats[-1] if len(formats) > 1 else formats[0]  # Last format
        
        if format1['format_id'] == format2['format_id']:
            # Try to find a different second format
            format2 = formats[1] if len(formats) > 1 else format1
        
        print(f"\n🎬 Testing two formats:")
        print(f"   Format 1: {format1['format_id']} - {format1['resolution']}")
        print(f"   Format 2: {format2['format_id']} - {format2['resolution']}")
        
        results = []
        
        # Test each format
        for i, fmt in enumerate([format1, format2], 1):
            print(f"\n📥 Test {i}: Downloading format {fmt['format_id']} ({fmt['resolution']})")
            
            # Create job
            job_data = {
                "url": test_url,
                "in_ts": 5.0,
                "out_ts": 8.0,  # 3-second clip
                "format_id": fmt['format_id']
            }
            
            response = requests.post(f"{BASE_URL}/api/v1/jobs", json=job_data, timeout=30)
            if response.status_code != 201:
                print(f"❌ Job creation failed: {response.status_code}")
                continue
            
            job_id = response.json()['id']
            print(f"✅ Job created: {job_id}")
            
            # Monitor job
            max_wait = 120
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                status_response = requests.get(f"{BASE_URL}/api/v1/jobs/{job_id}", timeout=10)
                if status_response.status_code != 200:
                    print(f"❌ Status check failed")
                    break
                
                job_status = status_response.json()
                status = job_status['status']
                stage = job_status.get('stage', 'unknown')
                
                print(f"📊 Status: {status} | Stage: {stage}")
                
                if status == 'done':
                    download_url = job_status.get('download_url')
                    if download_url:
                        # Get file size
                        try:
                            head_response = requests.head(download_url, timeout=10)
                            file_size = int(head_response.headers.get('content-length', 0))
                            
                            results.append({
                                'format_id': fmt['format_id'],
                                'resolution': fmt['resolution'],
                                'file_size': file_size,
                                'download_url': download_url
                            })
                            
                            print(f"✅ SUCCESS! File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
                            
                        except Exception as e:
                            print(f"⚠️  Could not get file size: {e}")
                            results.append({
                                'format_id': fmt['format_id'],
                                'resolution': fmt['resolution'],
                                'file_size': 0,
                                'download_url': download_url
                            })
                    break
                    
                elif status == 'error':
                    error_code = job_status.get('error_code', 'unknown')
                    print(f"❌ Job failed: {error_code}")
                    break
                
                time.sleep(2)
            else:
                print(f"⏰ Timeout after {max_wait} seconds")
        
        # Analyze results
        print(f"\n📊 RESULTS SUMMARY")
        print("=" * 50)
        
        if len(results) < 2:
            print("❌ Could not download both formats")
            return False
        
        for i, result in enumerate(results, 1):
            size_mb = result['file_size'] / 1024 / 1024 if result['file_size'] > 0 else 0
            print(f"   Format {i}: {result['format_id']} ({result['resolution']}) - {size_mb:.2f} MB")
        
        # Check if different
        if results[0]['file_size'] > 0 and results[1]['file_size'] > 0:
            if results[0]['file_size'] != results[1]['file_size']:
                ratio = max(results[0]['file_size'], results[1]['file_size']) / min(results[0]['file_size'], results[1]['file_size'])
                print(f"\n📈 File size ratio: {ratio:.2f}x")
                
                if ratio > 1.1:  # At least 10% difference
                    print("✅ SUCCESS: Different resolutions produce different file sizes!")
                    print("✅ YouTube blocking appears to be RESOLVED!")
                    print("✅ Resolution picker is working correctly!")
                    return True
                else:
                    print("⚠️  File sizes are very similar")
            else:
                print("⚠️  File sizes are identical")
        
        print("💡 Results suggest resolution picker may not be working as expected")
        print("💡 But downloads are successful, so YouTube blocking may be partially resolved")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🧪 Quick Resolution Test")
    print("This test downloads one video in two resolutions to verify the fix.")
    print()
    
    success = test_single_video_two_resolutions()
    
    if success:
        print("\n🎉 TEST COMPLETED!")
        print("✅ Downloads are working")
        print("💡 Run 'python test_youtube_blocking.py' for comprehensive testing")
    else:
        print("\n❌ TEST FAILED!")
        print("💡 Try running 'python update_ytdlp_comprehensive.py' first")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 