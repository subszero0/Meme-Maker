#!/usr/bin/env python3
import yt_dlp

def test_instagram_audio_streams():
    url = 'https://www.instagram.com/reel/DHAwk1mS_5I/?igsh=dW1wdTQydzF6d2F3'
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("🔍 Extracting Instagram video info...")
            info = ydl.extract_info(url, download=False)
            
            print(f"\n=== VIDEO INFO ===")
            print(f"Title: {info.get('title', 'Unknown')}")
            print(f"Duration: {info.get('duration', 'Unknown')} seconds")
            
            formats = info.get('formats', [])
            print(f"Total formats: {len(formats)}")
            
            # Categorize formats
            video_only = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') == 'none']
            audio_only = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
            combined = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
            
            print(f"\n=== FORMAT ANALYSIS ===")
            print(f"Video-only formats: {len(video_only)}")
            print(f"Audio-only formats: {len(audio_only)}")
            print(f"Combined A+V formats: {len(combined)}")
            
            print(f"\n=== SAMPLE FORMATS ===")
            for i, fmt in enumerate(formats[:5]):
                format_id = fmt.get('format_id', 'unknown')
                ext = fmt.get('ext', 'unknown')
                resolution = fmt.get('resolution', 'audio')
                vcodec = fmt.get('vcodec', 'none')
                acodec = fmt.get('acodec', 'none')
                filesize = fmt.get('filesize_approx', 'unknown')
                
                print(f"Format {i+1}: ID={format_id}, ext={ext}, resolution={resolution}")
                print(f"  -> Video: {vcodec}, Audio: {acodec}, Size: {filesize}")
            
            # Test what format would be selected by default
            print(f"\n=== DEFAULT FORMAT SELECTION ===")
            best_format = ydl.process_info(info)
            if 'format_id' in best_format:
                print(f"Default format would be: {best_format['format_id']}")
                print(f"Default vcodec: {best_format.get('vcodec', 'none')}")
                print(f"Default acodec: {best_format.get('acodec', 'none')}")
            
            # Check if this is a DASH scenario
            if len(video_only) > 0 and len(audio_only) > 0:
                print(f"\n⚠️  DASH SCENARIO DETECTED!")
                print(f"This video has separate audio and video streams.")
                print(f"yt-dlp will need to merge them during download.")
                
                # Show best video and audio formats
                if video_only:
                    best_video = max(video_only, key=lambda x: x.get('height', 0) or 0)
                    print(f"Best video format: {best_video.get('format_id')} ({best_video.get('resolution')})")
                
                if audio_only:
                    best_audio = max(audio_only, key=lambda x: x.get('abr', 0) or 0)
                    print(f"Best audio format: {best_audio.get('format_id')} ({best_audio.get('abr', 'unknown')} kbps)")
            
            elif len(combined) > 0:
                print(f"\n✅ COMBINED FORMATS AVAILABLE")
                print(f"Video has pre-merged audio+video streams.")
                best_combined = max(combined, key=lambda x: x.get('height', 0) or 0)
                print(f"Best combined format: {best_combined.get('format_id')} ({best_combined.get('resolution')})")
            
            else:
                print(f"\n❌ NO AUDIO DETECTED")
                print(f"This video appears to have no audio streams!")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_instagram_audio_streams() 