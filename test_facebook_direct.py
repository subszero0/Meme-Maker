import subprocess
import json
import sys

def test_facebook_direct():
    # Test a variety of Facebook URLs
    test_urls = [
        "https://www.facebook.com/watch/?v=1014329902448739",
        "https://www.facebook.com/watch/?v=321807423481765",  # Try another one
        "https://www.facebook.com/reel/1630821264129059"      # Try a reel
    ]
    
    for url in test_urls:
        print(f"🔍 Testing direct yt-dlp extraction: {url}")
        print("="*60)
        
        try:
            # Run yt-dlp directly to see what it extracts
            cmd = [
                "yt-dlp", 
                "--dump-json", 
                "--no-download",
                "--ignore-errors",
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                print(f"❌ yt-dlp failed: {result.stderr}")
                continue
                
            if not result.stdout.strip():
                print(f"❌ No output from yt-dlp")
                continue
                
            # Parse the JSON output
            data = json.loads(result.stdout)
            formats = data.get('formats', [])
            
            print(f"📊 Raw yt-dlp formats: {len(formats)}")
            
            if len(formats) == 0:
                print("❌ No formats found by yt-dlp")
                continue
                
            audio_only = []
            video_only = []
            merged = []
            
            for fmt in formats:
                vcodec = fmt.get('vcodec', 'none')
                acodec = fmt.get('acodec', 'none')
                format_id = fmt.get('format_id', 'unknown')
                url_present = bool(fmt.get('url'))
                
                if vcodec == 'none' and acodec != 'none':
                    audio_only.append((format_id, acodec, url_present))
                elif vcodec != 'none' and acodec == 'none':
                    video_only.append((format_id, vcodec, url_present))
                elif vcodec != 'none' and acodec != 'none':
                    merged.append((format_id, vcodec, acodec, url_present))
            
            print(f"🎵 Audio-only: {len(audio_only)}")
            for fid, acodec, has_url in audio_only:
                print(f"   {fid}: {acodec} | URL: {has_url}")
                
            print(f"📹 Video-only: {len(video_only)}")
            for fid, vcodec, has_url in video_only:
                print(f"   {fid}: {vcodec} | URL: {has_url}")
                
            print(f"🎬 Merged: {len(merged)}")
            for fid, vcodec, acodec, has_url in merged:
                print(f"   {fid}: {vcodec}+{acodec} | URL: {has_url}")
            
            if len(audio_only) == 0 and len(merged) == 0:
                print("🚨 NO AUDIO FORMATS FOUND - Facebook may not provide separate audio!")
            
            print("="*60)
            return  # Exit after first successful extraction
            
        except subprocess.TimeoutExpired:
            print("❌ yt-dlp timed out")
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()

if __name__ == "__main__":
    test_facebook_direct() 