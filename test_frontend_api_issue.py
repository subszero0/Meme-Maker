#!/usr/bin/env python3
"""
Frontend API Race Condition Test
Following Best Practice #5: Write failing test first

This test reproduces the frontend issue where ResolutionSelector
makes multiple rapid API calls causing race conditions and errors.
"""

import asyncio
import aiohttp
import time
from datetime import datetime

BACKEND_URL = "http://localhost:8000"
TEST_VIDEO_URL = "https://www.youtube.com/watch?v=TzUWcoI9TpA"

async def simulate_race_condition():
    """
    Simulate the frontend race condition by making multiple 
    simultaneous API calls to the metadata endpoint
    """
    print(f"\n🧪 SIMULATING FRONTEND RACE CONDITION")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Simulate what happens when ResolutionSelector makes multiple rapid calls
    tasks = []
    
    async with aiohttp.ClientSession() as session:
        # Create 5 simultaneous requests (simulating rapid user interactions)
        for i in range(5):
            task = make_metadata_request(session, i)
            tasks.append(task)
        
        # Execute all requests simultaneously
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        successful = 0
        failed = 0
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed += 1
                errors.append(f"Request {i+1}: {str(result)}")
                print(f"❌ Request {i+1}: FAILED - {str(result)}")
            else:
                successful += 1
                print(f"✅ Request {i+1}: SUCCESS")
        
        print(f"\n📊 RACE CONDITION RESULTS:")
        print(f"Successful: {successful}/{len(tasks)}")
        print(f"Failed: {failed}/{len(tasks)}")
        
        if failed > 0:
            print(f"\n❌ RACE CONDITION DETECTED - Multiple requests failed")
            print("This simulates the frontend issue!")
            return False
        else:
            print(f"\n✅ NO RACE CONDITION - All requests succeeded")
            return True

async def make_metadata_request(session, request_id):
    """Make a single metadata request"""
    try:
        start_time = time.time()
        payload = {"url": TEST_VIDEO_URL}
        
        async with session.post(
            f"{BACKEND_URL}/api/v1/metadata/extract",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if response.status == 200:
                data = await response.json()
                duration = time.time() - start_time
                print(f"🔍 Request {request_id+1}: {response.status} in {duration:.2f}s")
                return data
            else:
                text = await response.text()
                raise Exception(f"HTTP {response.status}: {text}")
                
    except asyncio.TimeoutError:
        raise Exception("Request timeout")
    except Exception as e:
        raise Exception(f"Network error: {str(e)}")

def test_sequential_requests():
    """Test sequential requests (should work fine)"""
    print(f"\n🧪 TESTING SEQUENTIAL REQUESTS")
    print("=" * 60)
    
    import requests
    
    for i in range(3):
        try:
            start_time = time.time()
            response = requests.post(
                f"{BACKEND_URL}/api/v1/metadata/extract",
                json={"url": TEST_VIDEO_URL},
                timeout=30
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                print(f"✅ Sequential request {i+1}: SUCCESS in {duration:.2f}s")
            else:
                print(f"❌ Sequential request {i+1}: FAILED - {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Sequential request {i+1}: ERROR - {str(e)}")
            return False
    
    print("✅ All sequential requests succeeded")
    return True

if __name__ == "__main__":
    print("🚀 FRONTEND API ISSUE REPRODUCTION TEST")
    
    # Test 1: Sequential requests (baseline)
    sequential_ok = test_sequential_requests()
    
    # Test 2: Concurrent requests (race condition simulation)
    concurrent_ok = asyncio.run(simulate_race_condition())
    
    print(f"\n{'='*60}")
    print("📊 FINAL TEST RESULTS")
    print('='*60)
    print(f"Sequential requests: {'✅ PASS' if sequential_ok else '❌ FAIL'}")
    print(f"Concurrent requests: {'✅ PASS' if concurrent_ok else '❌ FAIL'}")
    
    if sequential_ok and not concurrent_ok:
        print("\n🎯 ISSUE CONFIRMED: Frontend race condition reproduced!")
        print("💡 SOLUTION: Use React Query hooks to prevent multiple API calls")
    elif sequential_ok and concurrent_ok:
        print("\n✅ NO ISSUES: Both sequential and concurrent requests work")
    else:
        print("\n❌ BACKEND ISSUES: Sequential requests failing") 