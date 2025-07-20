#!/usr/bin/env python3
"""
Test fresh metadata extraction with cache bypass to test new format processing.
"""
import requests

def test_with_cache_bypass():
    """Test with cache completely bypassed."""
    
    # Use URL with parameter to bypass cache
    test_url = "https://www.facebook.com/reel/2797924943847507?bypass_cache=1"
    
    print("🔍 Testing with complete cache bypass")
    print("=" * 50)
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/metadata/extract",
            json={"url": test_url},
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return
            
        data = response.json()
        formats = data.get('formats', [])
        
        print(f"✅ Got {len(formats)} formats")
        
        if formats:
            first_format = formats[0]
            print(f"🎖️ FIRST FORMAT:")
            print(f"  📋 ID: {first_format.get('format_id')}")
            print(f"  🔊 Audio Codec: {first_format.get('acodec')}")
            print(f"  📝 Note: {first_format.get('format_note')}")
            
            if first_format.get('acodec') == 'none':
                print("✅ NEW LOGIC WORKING: Audio codec correctly shows 'none'")
                print("✅ No longer artificially marking video-only streams as having audio")
            else:
                print("❌ Still showing artificial audio codec")
                
        # Show all formats
        print("\n📋 ALL FORMATS:")
        for i, fmt in enumerate(formats[:5]):
            acodec = fmt.get('acodec', 'none')
            note = fmt.get('format_note', '')[:50]
            print(f"  {i+1}. acodec={acodec:8s} note={note}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_with_cache_bypass() 