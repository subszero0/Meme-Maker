import requests
import json

def check_facebook_metadata():
    # Try multiple Facebook URLs
    urls = [
        "https://www.facebook.com/watch/?v=1014329902448739",
        "https://www.facebook.com/100044283942799/videos/meresawaalka-most-viewed-video/"
    ]
    
    for url in urls:
        print(f"🔍 Testing Facebook URL: {url}")
        
        try:
            response = requests.post(
                'http://localhost:8000/api/v1/metadata/extract',
                json={'url': url},
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ Error: {response.status_code} - {response.text[:200]}")
                continue
            
            data = response.json()
            formats = data['formats']
            
            print(f"📊 Total formats returned: {len(formats)}")
            print()
            
            audio_only_count = 0
            video_only_count = 0
            merged_count = 0
            
            for i, fmt in enumerate(formats):
                format_id = fmt['format_id']
                vcodec = fmt['vcodec']
                acodec = fmt['acodec']
                url_present = bool(fmt.get('url'))
                resolution = fmt.get('resolution', 'N/A')
                
                if vcodec == 'none' and acodec != 'none':
                    audio_only_count += 1
                    print(f"🎵 AUDIO-ONLY #{i+1}: {format_id} | acodec:{acodec} | url:{url_present} | res:{resolution}")
                elif vcodec != 'none' and acodec == 'none':
                    video_only_count += 1
                    print(f"📹 VIDEO-ONLY #{i+1}: {format_id} | vcodec:{vcodec} | url:{url_present} | res:{resolution}")
                elif vcodec != 'none' and acodec != 'none':
                    merged_count += 1
                    print(f"🎬 MERGED #{i+1}: {format_id} | vcodec:{vcodec} | acodec:{acodec} | url:{url_present} | res:{resolution}")
                else:
                    print(f"❓ UNKNOWN #{i+1}: {format_id} | vcodec:{vcodec} | acodec:{acodec} | url:{url_present} | res:{resolution}")
            
            print()
            print(f"📈 Summary:")
            print(f"   Audio-only: {audio_only_count}")
            print(f"   Video-only: {video_only_count}")
            print(f"   Merged: {merged_count}")
            print(f"   Total: {len(formats)}")
            
            if audio_only_count == 0:
                print("🚨 NO AUDIO-ONLY FORMATS FOUND - This explains why frontend has no audio!")
            else:
                print("✅ Audio-only formats are present")
                # Check if the audio formats have valid URLs
                for i, fmt in enumerate(formats):
                    if fmt['vcodec'] == 'none' and fmt['acodec'] != 'none':
                        url = fmt.get('url', '')
                        if url and url.startswith('http'):
                            print(f"   ✅ Audio format {i+1} has valid HTTP URL")
                        else:
                            print(f"   ❌ Audio format {i+1} missing valid URL: {url[:50]}...")
            
            print("="*60)
            return  # Success, exit after first working URL
            
        except Exception as e:
            print(f"❌ Exception: {e}")
            continue

if __name__ == "__main__":
    check_facebook_metadata() 