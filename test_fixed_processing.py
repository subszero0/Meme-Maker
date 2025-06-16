#!/usr/bin/env python3
"""
Test the fixed video processing with the problematic URL
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"
PROBLEM_URL = "https://www.youtube.com/watch?v=vEy6tcU6eLU"

def test_fixed_processing():
    """Test the complete pipeline with the URL that was failing"""
    print(f"🚀 Testing fixed video processing with problematic URL")
    print(f"📋 URL: {PROBLEM_URL}")
    print("=" * 60)
    
    # Step 1: Get formats from backend
    print("🔍 Step 1: Getting formats from backend...")
    try:
        response = requests.post(f"{BASE_URL}/api/v1/metadata/extract", 
                               json={"url": PROBLEM_URL}, 
                               timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Metadata failed: {response.status_code}")
            return False
        
        data = response.json()
        formats = data.get('formats', [])
        
        if not formats:
            print("❌ No formats available")
            return False
        
        # Show what backend returns
        print(f"✅ Backend returned {len(formats)} formats:")
        for i, fmt in enumerate(formats[:5]):
            print(f"  {i+1}. {fmt['format_id']} - {fmt['resolution']}")
        
        # Try format 232 (the problematic one) 
        format_232 = None
        for fmt in formats:
            if fmt['format_id'] == '232':
                format_232 = fmt
                break
        
        if format_232:
            print(f"🎯 Found format 232 in backend response: {format_232['resolution']}")
            selected_format_id = '232'
        else:
            # Use first available format
            selected_format_id = formats[0]['format_id']
            print(f"🎯 Format 232 not found, using: {selected_format_id}")
        
    except Exception as e:
        print(f"❌ Metadata error: {e}")
        return False
    
    # Step 2: Submit processing job
    print(f"\n🎬 Step 2: Submitting processing job with format {selected_format_id}...")
    try:
        job_response = requests.post(f"{BASE_URL}/api/v1/jobs", json={
            "url": PROBLEM_URL,
            "in_ts": 4,
            "out_ts": 8,
            "format_id": selected_format_id
        }, timeout=30)
        
        if job_response.status_code not in [200, 201]:
            print(f"❌ Job creation failed: {job_response.status_code}")
            print(f"Response: {job_response.text}")
            return False
        
        job_data = job_response.json()
        job_id = job_data.get('id') or job_data.get('jobId')  # Handle both response formats
        print(f"✅ Job created: {job_id}")
        
    except Exception as e:
        print(f"❌ Job creation error: {e}")
        return False
    
    # Step 3: Monitor job progress
    print(f"\n📊 Step 3: Monitoring job progress...")
    max_wait = 300  # 5 minutes max
    start_time = time.time()
    last_progress = None
    last_stage = None
    
    while time.time() - start_time < max_wait:
        try:
            status_response = requests.get(f"{BASE_URL}/api/v1/jobs/{job_id}", timeout=10)
            
            if status_response.status_code != 200:
                print(f"❌ Status check failed: {status_response.status_code}")
                return False
            
            status_data = status_response.json()
            status = status_data.get('status')
            progress = status_data.get('progress')
            stage = status_data.get('stage')
            
            # Only print when progress or stage changes
            if progress != last_progress or stage != last_stage:
                progress_str = f"{progress}%" if progress is not None else "unknown"
                stage_str = stage if stage else "processing"
                print(f"  📈 Progress: {progress_str} - {stage_str}")
                last_progress = progress
                last_stage = stage
            
            if status == 'done':
                download_url = status_data.get('download_url')
                print(f"✅ Job completed successfully!")
                print(f"📥 Download URL: {download_url}")
                return True
            elif status == 'error':
                error_code = status_data.get('error_code', 'unknown')
                error_message = status_data.get('error_message', 'unknown error')
                print(f"❌ Job failed: {error_code}")
                print(f"📋 Error: {error_message}")
                return False
            
            time.sleep(2)  # Check every 2 seconds
            
        except Exception as e:
            print(f"❌ Status check error: {e}")
            time.sleep(5)
            continue
    
    print(f"⏰ Job timed out after {max_wait} seconds")
    return False

def main():
    """Run the test"""
    success = test_fixed_processing()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 SUCCESS! Video processing now works with the problematic URL")
        print("✅ The format validation and fallback system is working")
    else:
        print("❌ FAILED! Issue still exists or new problem found")
        print("🔍 Check the logs above for details")

if __name__ == "__main__":
    main() 