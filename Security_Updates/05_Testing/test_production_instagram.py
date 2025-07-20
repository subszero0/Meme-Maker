#!/usr/bin/env python3
"""
Test Production Instagram API
Tests the failing Instagram URLs against the production API
"""

import requests
import json

# The three failing URLs from the user
FAILING_URLS = [
    "https://www.instagram.com/reel/DLfPgczIp-x/?igsh=NWExNzlwb3h5YnJn",
    "https://www.instagram.com/reel/DLjuZlDTrq3/?igsh=MXIxNGNrenp4bGF5aw==", 
    "https://www.instagram.com/reel/DLiGaJABO_a/?igsh=MWQwc3BqcHA2M2k3Mw=="
]

# Using IP address from previous investigation
PRODUCTION_URL = "http://13.126.173.223:8000/api/v1/metadata"

def test_production_api(url):
    """Test URL against production API"""
    print(f"\n🌐 Testing production API for: {url}")
    
    payload = {"url": url}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(PRODUCTION_URL, json=payload, headers=headers, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS: {data.get('title', 'Unknown')}")
            print(f"⏱️ Duration: {data.get('duration', 'Unknown')}")
            return True
        else:
            try:
                error_data = response.json()
                print(f"❌ FAILED: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"❌ FAILED: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST FAILED: {str(e)}")
        return False

def main():
    print("🌐 Production Instagram API Test")
    print("=" * 50)
    
    results = {}
    
    for url in FAILING_URLS:
        print(f"\n{'='*60}")
        print(f"Testing URL: {url}")
        print(f"{'='*60}")
        
        results[url] = test_production_api(url)
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}")
    
    success_count = 0
    for url, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"\n📋 {url}: {status}")
        if success:
            success_count += 1
    
    print(f"\n📈 Results: {success_count}/{len(FAILING_URLS)} URLs successful")
    
    if success_count == 0:
        print("\n🚨 ALL PRODUCTION TESTS FAILED")
        print("This confirms the issue is in production environment, not the URLs themselves")
        print("Next steps:")
        print("1. Check production yt-dlp version")
        print("2. Verify Instagram cookie files in production")
        print("3. Check production Instagram configuration loading")
        print("4. Compare production vs local dependencies")
    else:
        print(f"\n✅ {success_count} URLs WORKING IN PRODUCTION")
        print("Production Instagram extraction is working!")
        
if __name__ == "__main__":
    main() 