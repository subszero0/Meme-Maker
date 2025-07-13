#!/usr/bin/env python3

import re

# Copy the exact regex from the backend
INSTAGRAM_URL_RE = re.compile(
    r"https?://(www\.)?instagram\.com/((reel|p|tv)/[\w\-]+)/?"
)

def test_instagram_regex():
    """Test Instagram regex pattern with underscore URLs"""
    
    print('🧪 Testing Instagram Regex Pattern')
    print('=' * 50)
    
    test_urls = [
        'https://www.instagram.com/reel/DLjuZlDTrq3/?igsh=MXIxNGNrenp4bGF5aw==',  # Working (no underscore)
        'https://www.instagram.com/reel/DLiGaJABO_a/?igsh=MWQwc3BqcHA2M2k3Mw==',  # Failing (with underscore)
        'https://www.instagram.com/reel/test_underscore/',  # Test underscore
        'https://www.instagram.com/reel/test-dash/',  # Test dash
        'https://www.instagram.com/reel/testNORMAL/',  # Test normal
    ]
    
    print('Regex pattern:', INSTAGRAM_URL_RE.pattern)
    print()
    
    for url in test_urls:
        match = INSTAGRAM_URL_RE.match(url)
        status = '✅ MATCH' if match else '❌ NO MATCH'
        print(f'{status}: {url}')
        if match:
            print(f'  Groups: {match.groups()}')
        print()
    
    # Test just the ID part
    print('🔍 Testing just the ID regex pattern:')
    id_pattern = re.compile(r'[\w\-]+')
    
    test_ids = ['DLjuZlDTrq3', 'DLiGaJABO_a', 'test_underscore', 'test-dash']
    
    for test_id in test_ids:
        match = id_pattern.fullmatch(test_id)
        status = '✅ MATCH' if match else '❌ NO MATCH'
        print(f'{status}: {test_id}')

if __name__ == '__main__':
    test_instagram_regex() 