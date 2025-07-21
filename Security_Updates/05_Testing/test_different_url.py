#!/usr/bin/env python3
"""
Test different YouTube URLs to see if the issue is URL-specific
"""
import requests
import time

TEST_URLS = [
    "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # Me at the zoo (oldest YouTube video)
    "https://www.youtube.com/watch?v=9bZkp7q19f0",  # Gangnam Style  
    "https://www.youtube.com/watch?v=L_jWHffIx5E",  # Smash Mouth - All Star
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll (problematic one)
]

def test_url(url, name):
    """Test a specific URL"""
    print(f"\n🎬 Testing: {name}")
    print(f"   URL: {url}")
    
    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:8000/api/v1/metadata/extract",
            json={"url": url},
            timeout=30
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success in {elapsed:.2f}s")
            print(f"   📺 Title: {data.get('title', 'N/A')[:60]}...")
            print(f"   ⏱️ Duration: {data.get('duration', 0)}s")
            print(f"   🎯 Formats: {len(data.get('formats', []))}")
            return True, elapsed, len(data.get('formats', []))
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"   💬 Error: {response.text[:100]}...")
            return False, elapsed, 0
            
    except requests.exceptions.Timeout:
        print(f"   ⏱️ Timeout after 30s")
        return False, 30, 0
    except Exception as e:
        print(f"   💥 Error: {e}")
        return False, 0, 0

def main():
    print("🚀 Testing Different YouTube URLs")
    print("=" * 50)
    
    results = []
    
    for i, url in enumerate(TEST_URLS):
        name = [
            "Me at the zoo (2005)",
            "Gangnam Style", 
            "Smash Mouth - All Star",
            "Rick Roll (Problematic)"
        ][i]
        
        success, elapsed, formats = test_url(url, name)
        results.append((name, success, elapsed, formats))
    
    print(f"\n📊 Summary")
    print("=" * 30)
    
    successful = 0
    total_time = 0
    
    for name, success, elapsed, formats in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}: {elapsed:.1f}s, {formats} formats")
        if success:
            successful += 1
            total_time += elapsed
    
    print(f"\n🎯 Results: {successful}/{len(TEST_URLS)} successful")
    if successful > 0:
        avg_time = total_time / successful
        print(f"📈 Average time: {avg_time:.1f}s")
        
        if avg_time < 10:
            print("🟢 Performance: GOOD")
        elif avg_time < 20:
            print("🟡 Performance: ACCEPTABLE") 
        else:
            print("🔴 Performance: NEEDS IMPROVEMENT")

if __name__ == "__main__":
    main() 