#!/usr/bin/env python3

import yt_dlp
import traceback

def test_failing_instagram_url():
    """Test the failing Instagram URL with backend configuration to identify exact error"""
    
    failing_url = 'https://www.instagram.com/reel/DLiGaJABO_a/?igsh=MWQwc3BqcHA2M2k3Mw=='
    
    print('🔍 Testing Failing URL with Backend Instagram Config')
    print('=' * 60)
    
    # Use the exact Instagram-specific configuration from our backend
    instagram_base_headers = {
        'User-Agent': (
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) '
            'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
        ),
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.instagram.com/',
    }
    
    instagram_opts = {
        'quiet': False,  # Enable verbose for debugging
        'no_warnings': False,
        'extract_flat': False,
        'skip_download': True,
        'http_headers': instagram_base_headers,
        'socket_timeout': 120,
        'retries': 3,
    }
    
    print(f'URL: {failing_url}')
    print(f'Config: Instagram-specific with headers and 120s timeout')
    print('=' * 60)
    
    ydl = yt_dlp.YoutubeDL(instagram_opts)
    
    try:
        info = ydl.extract_info(failing_url, download=False)
        print('✅ SUCCESS - This means the issue is production environment specific')
        print(f'Title: {info.get("title", "No title")}')
        print(f'Duration: {info.get("duration", "No duration")} seconds')
        return True
        
    except Exception as e:
        print('❌ FAILED - This explains the production 503 error')
        print(f'Error type: {type(e).__name__}')
        print(f'Error message: {str(e)}')
        print()
        
        # Analyze the error message for specific patterns
        error_str = str(e).lower()
        print('🔍 Error Analysis:')
        
        if 'login' in error_str or 'authentication' in error_str or 'cookies' in error_str or 'sign in' in error_str:
            print('- Authentication error detected')
            print('- Should return 429 in production')
        elif 'timeout' in error_str or 'timed out' in error_str:
            print('- Timeout error detected')
            print('- Should return 504 in production')
        elif 'private' in error_str or 'unavailable' in error_str:
            print('- Content unavailable error detected')
            print('- Currently falls through to 503 generic error')
        elif 'rate limit' in error_str or 'too many requests' in error_str:
            print('- Rate limiting error detected')
            print('- Should return 429 in production')
        else:
            print('- Unhandled error type - falls through to 503 generic error')
            print('- This is likely why we\'re seeing 503 in production')
        
        print()
        print('Full traceback:')
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_failing_instagram_url() 