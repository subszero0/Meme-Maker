#!/usr/bin/env python3
"""
Test Script: Stage 2 - Detailed Metadata with Formats
================================================================

This script tests the detailed metadata endpoint (/api/v1/metadata/extract) to verify:
1. The endpoint is accessible 
2. Format extraction works correctly
3. Performance timing
4. Data structure matches frontend expectations
"""

import requests
import json
import time
from datetime import datetime

# Configuration  
API_BASE_URL = "http://localhost:8000"
TEST_URL = "https://www.youtube.com/watch?v=cqvjbDdiCCQ"

def test_detailed_metadata():
    """Test the detailed metadata extraction endpoint"""
    print(f"=== Stage 2: Detailed Metadata with Formats Test ===")
    print(f"Timestamp: {datetime.now()}")
    print(f"Testing URL: {TEST_URL}")
    print(f"API Base: {API_BASE_URL}")
    print("")
    
    # Test data matching UrlRequest model (not MetadataRequest!)
    request_data = {
        "url": TEST_URL
    }
    
    print(f"1. Sending request to /api/v1/metadata/extract")
    print(f"   Request payload: {json.dumps(request_data, indent=2)}")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/metadata/extract",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=60  # Increased timeout for detailed extraction
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"2. Response received in {duration:.2f} seconds")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS - Detailed metadata extracted!")
            print(f"   Title: {data.get('title', 'N/A')}")
            print(f"   Duration: {data.get('duration', 'N/A')} seconds")
            print(f"   Uploader: {data.get('uploader', 'N/A')}")
            print(f"   View Count: {data.get('view_count', 'N/A')}")
            print(f"   Upload Date: {data.get('upload_date', 'N/A')}")
            
            formats = data.get('formats', [])
            print(f"   Formats Found: {len(formats)}")
            
            if formats:
                print(f"   Top 5 Formats:")
                for i, fmt in enumerate(formats[:5]):
                    print(f"     {i+1}. ID: {fmt.get('format_id')} | "
                          f"Resolution: {fmt.get('resolution')} | "
                          f"Codec: {fmt.get('vcodec')}/{fmt.get('acodec')} | "
                          f"Note: {fmt.get('format_note', 'N/A')}")
                          
                # Test data structure matches frontend expectations
                required_fields = ['format_id', 'ext', 'resolution', 'vcodec', 'acodec', 'format_note']
                first_format = formats[0]
                missing_fields = [field for field in required_fields if field not in first_format]
                
                if missing_fields:
                    print(f"⚠️  WARNING - Missing fields in format: {missing_fields}")
                else:
                    print(f"✅ Format structure is complete")
                    
            else:
                print(f"⚠️  WARNING - No formats found!")
                
            return True, duration, len(formats)
        else:
            print(f"❌ FAILED - HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False, duration, 0
            
    except requests.exceptions.Timeout:
        end_time = time.time()
        duration = end_time - start_time
        print(f"❌ TIMEOUT after {duration:.2f} seconds")
        return False, duration, 0
        
    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR - Is the backend running?")
        return False, 0, 0
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"❌ UNEXPECTED ERROR after {duration:.2f} seconds: {e}")
        return False, duration, 0

def test_health_first():
    """Test if backend is running"""
    print(f"0. Health Check")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Backend is running")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except:
        print(f"❌ Backend is not accessible")
        return False

def test_multiple_runs():
    """Test multiple runs to check consistency"""
    print(f"\n=== Multiple Runs Test ===")
    times = []
    format_counts = []
    
    for i in range(3):
        print(f"\nRun {i+1}/3:")
        success, duration, format_count = test_detailed_metadata()
        if success:
            times.append(duration)
            format_counts.append(format_count)
        else:
            print(f"❌ Run {i+1} failed")
            return False
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n📊 Performance Summary:")
        print(f"   Average Time: {avg_time:.2f}s")
        print(f"   Min Time: {min_time:.2f}s")
        print(f"   Max Time: {max_time:.2f}s")
        print(f"   Format Counts: {format_counts}")
        
        # Performance thresholds
        if avg_time > 15:
            print(f"⚠️  WARNING - Average response time too slow: {avg_time:.2f}s")
        if max_time > 30:
            print(f"⚠️  WARNING - Max response time too slow: {max_time:.2f}s")
            
        # Consistency check
        if len(set(format_counts)) > 1:
            print(f"⚠️  WARNING - Inconsistent format counts across runs")
        
        return True
    
    return False

if __name__ == "__main__":
    print("=" * 60)
    print("METADATA EXTRACTION - STAGE 2 TEST")
    print("=" * 60)
    
    if not test_health_first():
        print("\n🛑 Cannot proceed - backend not running")
        exit(1)
    
    print()
    success = test_multiple_runs()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ STAGE 2 PASSED - Detailed metadata extraction working")
    else:
        print("❌ STAGE 2 FAILED - Detailed metadata extraction broken")
    print("=" * 60) 