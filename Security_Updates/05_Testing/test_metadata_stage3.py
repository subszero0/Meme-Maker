#!/usr/bin/env python3
"""
Test Script: Stage 3 - Frontend API Integration
================================================================

This script tests the complete frontend API flow to identify:
1. Which API calls the frontend is actually making
2. Performance bottlenecks in the chain
3. Caching behavior
4. Error handling
"""

import requests
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration  
API_BASE_URL = "http://localhost:8000"
FRONTEND_BASE_URL = "http://localhost:3000"
TEST_URL = "https://www.youtube.com/watch?v=cqvjbDdiCCQ"

def simulate_frontend_flow():
    """Simulate the exact API flow the frontend would make"""
    print(f"=== Stage 3: Frontend API Flow Simulation ===")
    print(f"Timestamp: {datetime.now()}")
    print(f"Testing URL: {TEST_URL}")
    print("")
    
    results = {}
    
    # Step 1: URL Input - typically triggers metadata fetch
    print("1. 🎬 User inputs URL (simulating frontend behavior)")
    
    # Step 2: ResolutionSelector component calls getDetailedMetadata
    print("2. 🔍 ResolutionSelector: Fetching detailed metadata...")
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/metadata/extract",
            json={"url": TEST_URL},
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        metadata_time = time.time() - start_time
        results['metadata_fetch'] = {
            'success': response.status_code == 200,
            'time': metadata_time,
            'status_code': response.status_code
        }
        
        if response.status_code == 200:
            data = response.json()
            formats = data.get('formats', [])
            print(f"   ✅ Metadata fetched in {metadata_time:.2f}s")
            print(f"   📊 Found {len(formats)} formats")
            
            # Step 3: Frontend would process and display formats
            print("3. 🎨 Frontend processing formats for display...")
            
            # Group formats by resolution like the frontend does
            resolutions = {}
            for fmt in formats:
                resolution = fmt.get('resolution', 'unknown')
                if resolution not in resolutions:
                    resolutions[resolution] = []
                resolutions[resolution].append(fmt)
            
            print(f"   📊 Grouped into {len(resolutions)} unique resolutions")
            
            # Step 4: Auto-select preferred format (1080p > 720p > highest)
            print("4. 🎯 Auto-selecting preferred format...")
            
            preferred_format = None
            for fmt in formats:
                if '1080' in fmt.get('resolution', ''):
                    preferred_format = fmt
                    break
            
            if not preferred_format:
                for fmt in formats:
                    if '720' in fmt.get('resolution', ''):
                        preferred_format = fmt
                        break
            
            if not preferred_format and formats:
                preferred_format = formats[0]
            
            if preferred_format:
                print(f"   ✅ Auto-selected: {preferred_format.get('format_id')} "
                      f"({preferred_format.get('resolution')})")
                results['auto_selection'] = {
                    'format_id': preferred_format.get('format_id'),
                    'resolution': preferred_format.get('resolution')
                }
            else:
                print(f"   ❌ No format could be auto-selected")
                results['auto_selection'] = None
            
            # Step 5: User interaction simulation
            print("5. 👤 Simulating user format selection...")
            
            # Test changing format selection (this often triggers re-analysis)
            test_format = None
            for fmt in formats:
                if fmt.get('format_id') != preferred_format.get('format_id'):
                    test_format = fmt
                    break
            
            if test_format:
                print(f"   🔄 User selects different format: {test_format.get('format_id')} "
                      f"({test_format.get('resolution')})")
                
                # This shouldn't trigger another API call, but let's check if it would
                results['format_change'] = {
                    'new_format_id': test_format.get('format_id'),
                    'new_resolution': test_format.get('resolution')
                }
            
            return results
            
        else:
            print(f"   ❌ Metadata fetch failed: {response.status_code}")
            print(f"   Response: {response.text}")
            results['metadata_fetch']['error'] = response.text
            return results
            
    except Exception as e:
        metadata_time = time.time() - start_time
        print(f"   ❌ Error after {metadata_time:.2f}s: {e}")
        results['metadata_fetch'] = {
            'success': False,
            'time': metadata_time,
            'error': str(e)
        }
        return results

def test_concurrent_requests():
    """Test how the API handles concurrent requests (like multiple users)"""
    print(f"\n=== Concurrent Request Test ===")
    
    def make_request(request_id):
        start = time.time()
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/v1/metadata/extract",
                json={"url": TEST_URL},
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            duration = time.time() - start
            return {
                'id': request_id,
                'success': response.status_code == 200,
                'time': duration,
                'status': response.status_code
            }
        except Exception as e:
            duration = time.time() - start
            return {
                'id': request_id,
                'success': False,
                'time': duration,
                'error': str(e)
            }
    
    # Simulate 3 concurrent users
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(make_request, i) for i in range(3)]
        results = [future.result() for future in as_completed(futures)]
    
    # Analyze results
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    if successful:
        avg_time = sum(r['time'] for r in successful) / len(successful)
        max_time = max(r['time'] for r in successful)
        min_time = min(r['time'] for r in successful)
        
        print(f"📊 Concurrent Results:")
        print(f"   Successful: {len(successful)}/3")
        print(f"   Average Time: {avg_time:.2f}s")
        print(f"   Time Range: {min_time:.2f}s - {max_time:.2f}s")
        
        if max_time - min_time > 5:
            print(f"⚠️  WARNING - High time variance suggests resource contention")
    
    if failed:
        print(f"❌ Failed requests: {len(failed)}")
        for fail in failed:
            print(f"   Request {fail['id']}: {fail.get('error', 'Unknown error')}")
    
    return len(successful) == 3

def test_caching_behavior():
    """Test if repeated requests are cached"""
    print(f"\n=== Caching Behavior Test ===")
    
    times = []
    
    for i in range(3):
        print(f"Request {i+1}/3...")
        start = time.time()
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/v1/metadata/extract",
                json={"url": TEST_URL},
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            duration = time.time() - start
            times.append(duration)
            
            if response.status_code == 200:
                print(f"   ✅ Success in {duration:.2f}s")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                
        except Exception as e:
            duration = time.time() - start
            print(f"   ❌ Error in {duration:.2f}s: {e}")
            times.append(duration)
    
    if len(times) >= 2:
        first_time = times[0]
        subsequent_times = times[1:]
        avg_subsequent = sum(subsequent_times) / len(subsequent_times)
        
        print(f"📊 Caching Analysis:")
        print(f"   First request: {first_time:.2f}s")
        print(f"   Subsequent avg: {avg_subsequent:.2f}s")
        
        if avg_subsequent < first_time * 0.5:
            print(f"✅ Likely cached - significant speedup detected")
        elif avg_subsequent < first_time * 0.8:
            print(f"🤔 Possible caching - moderate speedup")
        else:
            print(f"❌ No caching detected - similar times")
    
    return times

def analyze_bottlenecks(results, concurrent_success, cache_times):
    """Analyze where the bottlenecks are"""
    print(f"\n=== Bottleneck Analysis ===")
    
    if 'metadata_fetch' in results:
        fetch_time = results['metadata_fetch'].get('time', 0)
        
        print(f"🔍 Performance Analysis:")
        print(f"   Metadata fetch time: {fetch_time:.2f}s")
        
        # Categorize performance
        if fetch_time > 30:
            print(f"🔴 CRITICAL - Very slow response (>{30}s)")
        elif fetch_time > 15:
            print(f"🟡 SLOW - Above acceptable threshold (>{15}s)")
        elif fetch_time > 5:
            print(f"🟠 ACCEPTABLE - Within range but could be faster")
        else:
            print(f"🟢 FAST - Good performance (<5s)")
    
    print(f"\n🎯 Recommendations:")
    
    # Specific recommendations based on findings
    if not concurrent_success:
        print(f"   - Add request queuing/rate limiting")
        print(f"   - Investigate resource contention")
    
    if cache_times and len(cache_times) > 1:
        if cache_times[1] >= cache_times[0] * 0.8:
            print(f"   - Implement response caching")
            print(f"   - Add Redis/in-memory cache")
    
    if 'metadata_fetch' in results and results['metadata_fetch'].get('time', 0) > 10:
        print(f"   - Optimize yt-dlp configuration")
        print(f"   - Add format filtering to reduce processing")
        print(f"   - Consider background pre-processing")

if __name__ == "__main__":
    print("=" * 60)
    print("FRONTEND API INTEGRATION - STAGE 3 TEST")
    print("=" * 60)
    
    # Test complete flow
    flow_results = simulate_frontend_flow()
    
    # Test concurrent behavior
    concurrent_success = test_concurrent_requests()
    
    # Test caching
    cache_times = test_caching_behavior()
    
    # Analyze bottlenecks and provide recommendations
    analyze_bottlenecks(flow_results, concurrent_success, cache_times)
    
    print("\n" + "=" * 60)
    
    # Overall assessment
    if (flow_results.get('metadata_fetch', {}).get('success', False) and 
        concurrent_success and 
        flow_results.get('auto_selection')):
        print("✅ STAGE 3 PASSED - Frontend integration working")
    else:
        print("❌ STAGE 3 FAILED - Issues in frontend integration")
    
    print("=" * 60) 