#!/usr/bin/env python3
"""
Debug script to test resolution picker functionality.
This will help identify exactly where the format_id is being lost.
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"
TEST_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll for testing

def test_metadata_extraction():
    """Test Step 1: Metadata extraction and format listing"""
    print("🔍 Step 1: Testing metadata extraction...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/metadata/extract", 
                               json={"url": TEST_URL}, 
                               timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Metadata extraction failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None, None
        
        data = response.json()
        formats = data.get('formats', [])
        
        print(f"✅ Metadata extraction successful!")
        print(f"📋 Found {len(formats)} formats:")
        
        for i, fmt in enumerate(formats):
            print(f"  {i+1}. {fmt['format_id']} - {fmt['resolution']} ({fmt.get('filesize', 'unknown size')})")
        
        if formats:
            best_format = formats[0]
            print(f"🎯 Best format: {best_format['format_id']} ({best_format['resolution']})")
            return data, best_format['format_id']
        else:
            print("❌ No formats found!")
            return data, None
            
    except Exception as e:
        print(f"❌ Metadata extraction error: {e}")
        return None, None

def test_job_creation(format_id):
    """Test Step 2: Job creation with format_id"""
    print(f"\n🚀 Step 2: Testing job creation with format_id: {format_id}")
    
    job_data = {
        "url": TEST_URL,
        "in_ts": 10.0,
        "out_ts": 20.0,
        "format_id": format_id
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/jobs", 
                               json=job_data, 
                               timeout=30)
        
        if response.status_code != 201:
            print(f"❌ Job creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
        
        job_response = response.json()
        job_id = job_response['id']
        returned_format_id = job_response.get('format_id')
        
        print(f"✅ Job created successfully!")
        print(f"📋 Job ID: {job_id}")
        print(f"📋 Sent format_id: {format_id}")
        print(f"📋 Returned format_id: {returned_format_id}")
        
        if returned_format_id != format_id:
            print(f"⚠️  WARNING: format_id mismatch! Sent: {format_id}, Got: {returned_format_id}")
        
        return job_id
        
    except Exception as e:
        print(f"❌ Job creation error: {e}")
        return None

def test_job_monitoring(job_id):
    """Test Step 3: Job monitoring and completion"""
    print(f"\n👀 Step 3: Monitoring job {job_id}...")
    
    max_wait = 300  # 5 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{BASE_URL}/api/v1/jobs/{job_id}", timeout=10)
            
            if response.status_code != 200:
                print(f"❌ Job status check failed: {response.status_code}")
                return False
            
            job_status = response.json()
            status = job_status['status']
            progress = job_status.get('progress', 0)
            stage = job_status.get('stage', 'unknown')
            
            print(f"📊 Status: {status} | Progress: {progress}% | Stage: {stage}")
            
            if status == 'done':
                print(f"✅ Job completed successfully!")
                download_url = job_status.get('download_url')
                if download_url:
                    print(f"📁 Download URL: {download_url}")
                return True
            elif status == 'error':
                error_code = job_status.get('error_code', 'unknown')
                print(f"❌ Job failed with error: {error_code}")
                return False
            
            time.sleep(5)  # Wait 5 seconds before next check
            
        except Exception as e:
            print(f"❌ Error checking job status: {e}")
            return False
    
    print(f"⏰ Job monitoring timed out after {max_wait} seconds")
    return False

def main():
    print("🧪 Resolution Picker Debug Test")
    print("=" * 50)
    
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print("✅ Backend is running")
    except:
        print("❌ Backend is not running! Please start Docker services.")
        print("\nTo start services:")
        print("1. Open PowerShell as Administrator")
        print("2. Navigate to project directory")
        print("3. Run: docker-compose up --build")
        return 1
    
    # Test Step 1: Metadata extraction
    metadata, format_id = test_metadata_extraction()
    if not metadata or not format_id:
        print("❌ Cannot proceed without valid metadata and format_id")
        return 1
    
    # Test Step 2: Job creation
    job_id = test_job_creation(format_id)
    if not job_id:
        print("❌ Cannot proceed without valid job_id")
        return 1
    
    # Test Step 3: Job monitoring
    success = test_job_monitoring(job_id)
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! Resolution picker should be working.")
    else:
        print("❌ Tests failed. Check the logs above for details.")
        print("\nDebugging tips:")
        print("1. Check Docker logs: docker-compose logs")
        print("2. Check browser console for frontend errors")
        print("3. Verify Docker services are all running: docker-compose ps")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 