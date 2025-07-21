#!/usr/bin/env python3
"""
Test script to check current performance of metadata endpoints
"""
import requests
import time
import json

# Test URLs
TEST_URLS = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll
    "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # Me at the zoo (short video)
    "https://www.youtube.com/watch?v=9bZkp7q19f0",  # Gangnam Style
]

BASE_URL = "http://localhost:8000"

def test_basic_metadata(url):
    """Test the basic metadata endpoint (/metadata)"""
    print(f"\n🔍 Testing basic metadata for: {url}")
    
    payload = {"url": url}
    
    start_time = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/metadata",
            json=payload,
            timeout=60
        )
        end_time = time.time()
        elapsed = end_time - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Basic metadata success in {elapsed:.2f}s")
            print(f"   Title: {data.get('title', 'N/A')}")
            print(f"   Duration: {data.get('duration', 0)}s")
            print(f"   Resolutions: {data.get('resolutions', [])}")
            return elapsed, True, len(data.get('resolutions', []))
        else:
            print(f"❌ Basic metadata failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return elapsed, False, 0
            
    except requests.exceptions.Timeout:
        print(f"⏱️ Basic metadata timeout after 60s")
        return 60, False, 0
    except Exception as e:
        print(f"💥 Basic metadata exception: {e}")
        return time.time() - start_time, False, 0

def test_detailed_metadata(url):
    """Test the detailed metadata endpoint (/metadata/extract)"""
    print(f"\n🔍 Testing detailed metadata for: {url}")
    
    payload = {"url": url}
    
    start_time = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/metadata/extract",
            json=payload,
            timeout=60
        )
        end_time = time.time()
        elapsed = end_time - start_time
        
        if response.status_code == 200:
            data = response.json()
            formats = data.get('formats', [])
            print(f"✅ Detailed metadata success in {elapsed:.2f}s")
            print(f"   Title: {data.get('title', 'N/A')}")
            print(f"   Duration: {data.get('duration', 0)}s")
            print(f"   Formats found: {len(formats)}")
            
            if formats:
                print(f"   First 3 formats:")
                for i, fmt in enumerate(formats[:3]):
                    print(f"     {i+1}. {fmt.get('format_id', 'N/A')}: {fmt.get('resolution', 'N/A')} ({fmt.get('vcodec', 'N/A')})")
            
            return elapsed, True, len(formats)
        else:
            print(f"❌ Detailed metadata failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return elapsed, False, 0
            
    except requests.exceptions.Timeout:
        print(f"⏱️ Detailed metadata timeout after 60s")
        return 60, False, 0
    except Exception as e:
        print(f"💥 Detailed metadata exception: {e}")
        return time.time() - start_time, False, 0

def test_cache_performance(url):
    """Test if caching is working by making the same request twice"""
    print(f"\n🔄 Testing cache performance for: {url}")
    
    # First request (should hit the API)
    print("   First request (cache miss expected):")
    elapsed1, success1, formats1 = test_detailed_metadata(url)
    
    if not success1:
        print("   ❌ First request failed, skipping cache test")
        return
    
    time.sleep(1)  # Brief pause
    
    # Second request (should hit cache)
    print("   Second request (cache hit expected):")
    elapsed2, success2, formats2 = test_detailed_metadata(url)
    
    if success2:
        cache_improvement = elapsed1 - elapsed2
        improvement_pct = (cache_improvement / elapsed1) * 100 if elapsed1 > 0 else 0
        
        if elapsed2 < elapsed1 * 0.5:  # 50% faster = likely cache hit
            print(f"   ✅ Cache working! {cache_improvement:.2f}s faster ({improvement_pct:.1f}% improvement)")
        else:
            print(f"   ⚠️ Cache may not be working. Difference: {cache_improvement:.2f}s")
    else:
        print("   ❌ Second request failed")

def main():
    print("🚀 Testing Current Performance of Metadata Endpoints")
    print("=" * 60)
    
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print(f"⚠️ Backend responded with status: {response.status_code}")
    except Exception as e:
        print(f"❌ Backend not reachable: {e}")
        return
    
    # Test with Rick Roll URL (the problematic one from your summary)
    test_url = TEST_URLS[0]
    
    print(f"\n📊 Performance Test Results")
    print("=" * 40)
    
    # Test basic metadata
    basic_elapsed, basic_success, basic_resolutions = test_basic_metadata(test_url)
    
    # Test detailed metadata
    detailed_elapsed, detailed_success, detailed_formats = test_detailed_metadata(test_url)
    
    # Test caching if detailed metadata worked
    if detailed_success:
        test_cache_performance(test_url)
    
    # Performance analysis
    print(f"\n📈 Performance Analysis")
    print("=" * 30)
    
    if basic_success:
        if basic_elapsed < 5:
            print(f"🟢 Basic metadata: GOOD ({basic_elapsed:.2f}s)")
        elif basic_elapsed < 15:
            print(f"🟡 Basic metadata: ACCEPTABLE ({basic_elapsed:.2f}s)")
        else:
            print(f"🔴 Basic metadata: SLOW ({basic_elapsed:.2f}s)")
    else:
        print(f"🔴 Basic metadata: FAILED")
    
    if detailed_success:
        if detailed_elapsed < 10:
            print(f"🟢 Detailed metadata: GOOD ({detailed_elapsed:.2f}s, {detailed_formats} formats)")
        elif detailed_elapsed < 20:
            print(f"🟡 Detailed metadata: ACCEPTABLE ({detailed_elapsed:.2f}s, {detailed_formats} formats)")
        else:
            print(f"🔴 Detailed metadata: SLOW ({detailed_elapsed:.2f}s, {detailed_formats} formats)")
    else:
        print(f"🔴 Detailed metadata: FAILED")
    
    # Recommendations
    print(f"\n💡 Recommendations")
    print("=" * 20)
    
    if not basic_success or not detailed_success:
        print("• Debug API failures - check backend logs")
        print("• Verify yt-dlp configuration and fallback logic")
    
    if basic_success and basic_elapsed > 10:
        print("• Basic metadata is too slow - investigate caching")
    
    if detailed_success and detailed_elapsed > 15:
        print("• Detailed metadata is slow - consider more aggressive optimization")
        
    if detailed_formats < 5:
        print("• Low format count - verify format filtering logic")

if __name__ == "__main__":
    main() 