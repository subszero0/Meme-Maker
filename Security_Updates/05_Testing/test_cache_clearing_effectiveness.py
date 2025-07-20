#!/usr/bin/env python3
"""
Cache Clearing Effectiveness Test

This script helps test whether cache clearing methods are working effectively
by providing specific instructions and validation steps.
"""

import time
import requests
from datetime import datetime

def test_api_response():
    """Test the current API response to see what we're getting"""
    try:
        url = "https://memeit.pro/api/v1/metadata"
        payload = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        
        start_time = time.time()
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        end_time = time.time()
        
        return {
            'status_code': response.status_code,
            'response_time': end_time - start_time,
            'headers': dict(response.headers),
            'body': response.text[:500] if response.text else '',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def print_cache_clearing_instructions():
    """Print step-by-step cache clearing instructions"""
    print("🧹 COMPREHENSIVE CACHE CLEARING TEST")
    print("=" * 50)
    print()
    print("Follow these steps IN ORDER and test after each level:")
    print()
    
    print("📋 LEVEL 1: Basic Chrome Settings Clear")
    print("1. Chrome → Settings → Privacy and security → Clear browsing data")
    print("2. Select 'Cached images and files' ONLY")
    print("3. Time range: 'All time'")
    print("4. Click 'Clear data'")
    print("5. ⚠️  Keep browser open, go to memeit.pro and test")
    print()
    
    print("📋 LEVEL 2: Hard Refresh (RECOMMENDED)")
    print("1. Go to memeit.pro")
    print("2. Press Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)")
    print("3. OR: Right-click refresh button → 'Empty Cache and Hard Reload'")
    print("4. Test immediately")
    print()
    
    print("📋 LEVEL 3: DevTools Cache Disable")
    print("1. Open DevTools (F12)")
    print("2. Go to Network tab")
    print("3. Check ☑️ 'Disable cache' checkbox")
    print("4. KEEP DevTools open")
    print("5. Refresh page and test")
    print("6. This prevents ALL caching while DevTools is open")
    print()
    
    print("📋 LEVEL 4: DevTools Complete Clear")
    print("1. Open DevTools (F12)")
    print("2. Right-click refresh button → 'Empty Cache and Hard Reload'")
    print("3. OR: DevTools → Application tab → Storage → 'Clear storage'")
    print("4. Test immediately")
    print()
    
    print("📋 LEVEL 5: Nuclear Option")
    print("1. Close ALL browser windows")
    print("2. Chrome → Settings → Privacy → Clear browsing data")
    print("3. Select ALL items, time range: 'All time'")
    print("4. Clear data")
    print("5. Restart Chrome completely")
    print("6. Open in Incognito/Private mode")
    print("7. Go to memeit.pro and test")
    print()
    
    print("📋 LEVEL 6: Different Browser Test")
    print("1. Open Firefox/Edge/Safari")
    print("2. Go to memeit.pro")
    print("3. Test - if this works, it confirms Chrome cache issue")
    print()

def main():
    print("🔍 CACHE CLEARING EFFECTIVENESS TEST")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # First, test current API state
    print("🧪 Testing current API state...")
    baseline = test_api_response()
    
    if 'error' in baseline:
        print(f"❌ API test failed: {baseline['error']}")
        print("   Check internet connection and try again")
        return
    
    print(f"📊 Baseline API Response:")
    print(f"   Status: {baseline['status_code']}")
    print(f"   Response time: {baseline['response_time']:.2f}s")
    if baseline['status_code'] == 200:
        print(f"   ✅ API is working - no cache clearing needed")
    elif baseline['status_code'] == 400:
        print(f"   ⚠️  Expected error (YouTube bot detection)")
        print(f"   Response: {baseline['body'][:100]}...")
    else:
        print(f"   ❓ Unexpected status: {baseline['status_code']}")
    
    print()
    print_cache_clearing_instructions()
    
    print("🎯 TESTING INSTRUCTIONS:")
    print("1. After each cache clearing level, come back here")
    print("2. Press Enter to test the API again")
    print("3. Compare results to see if cache clearing worked")
    print("4. If results change, that level of cache clearing was effective")
    print()
    
    level = 1
    while True:
        input(f"📋 Press Enter after completing Level {level} cache clearing (or 'q' to quit): ")
        
        if input().lower().strip() == 'q':
            break
            
        print(f"\n🧪 Testing after Level {level} cache clearing...")
        result = test_api_response()
        
        if 'error' in result:
            print(f"❌ Test failed: {result['error']}")
        else:
            print(f"📊 Results after Level {level}:")
            print(f"   Status: {result['status_code']}")
            print(f"   Response time: {result['response_time']:.2f}s")
            
            # Compare with baseline
            if result['status_code'] != baseline['status_code']:
                print(f"   🔄 Status changed from {baseline['status_code']} to {result['status_code']}")
                print(f"   ✅ Cache clearing Level {level} was EFFECTIVE!")
            elif abs(result['response_time'] - baseline['response_time']) > 1.0:
                print(f"   ⏱️  Response time changed significantly")
                print(f"   ✅ Cache clearing Level {level} had some effect")
            else:
                print(f"   ➡️  No significant change detected")
                print(f"   ⚠️  Try the next level of cache clearing")
        
        level += 1
        if level > 6:
            print("\n🏁 All cache clearing levels completed!")
            print("If the issue persists after Level 5, it's likely NOT a cache issue.")
            break
    
    print(f"\n✅ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 