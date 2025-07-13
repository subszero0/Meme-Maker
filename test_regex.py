#!/usr/bin/env python3

import re

def test_instagram_regex():
    """Test Instagram URL regex with working and failing URLs"""
    
    # Current regex pattern from backend
    INSTAGRAM_URL_RE = re.compile(
        r"https?://(www\.)?instagram\.com/((reel|p|tv)/[\w\-]+)/?"
    )
    
    working_url = 'https://www.instagram.com/reel/DLjuZlDTrq3/?igsh=MXIxNGNrenp4bGF5aw=='
    failing_url = 'https://www.instagram.com/reel/DLiGaJABO_a/?igsh=MWQwc3BqcHA2M2k3Mw=='
    
    print('🔍 Regex Testing for Instagram URLs')
    print('=' * 50)
    print(f'Pattern: {INSTAGRAM_URL_RE.pattern}')
    print()
    
    # Test working URL
    working_match = INSTAGRAM_URL_RE.match(working_url)
    print(f'Working URL: {working_url}')
    print(f'Match result: {bool(working_match)}')
    if working_match:
        print(f'Matched groups: {working_match.groups()}')
    print()
    
    # Test failing URL
    failing_match = INSTAGRAM_URL_RE.match(failing_url)
    print(f'Failing URL: {failing_url}')
    print(f'Match result: {bool(failing_match)}')
    if failing_match:
        print(f'Matched groups: {failing_match.groups()}')
    print()
    
    # Test just the ID parts
    working_id = 'DLjuZlDTrq3'
    failing_id = 'DLiGaJABO_a'
    
    id_pattern = re.compile(r'[\w\-]+')
    print('🔍 Testing just the ID patterns:')
    print(f'Working ID "{working_id}": {bool(id_pattern.fullmatch(working_id))}')
    print(f'Failing ID "{failing_id}": {bool(id_pattern.fullmatch(failing_id))}')
    print()
    
    # Test with different pattern
    better_pattern = re.compile(r'[\w_\-]+')
    print('🔍 Testing with explicit underscore pattern [\w_\-]+:')
    print(f'Working ID "{working_id}": {bool(better_pattern.fullmatch(working_id))}')
    print(f'Failing ID "{failing_id}": {bool(better_pattern.fullmatch(failing_id))}')
    print()
    
    if not failing_match:
        print('❌ ISSUE FOUND: Failing URL does not match regex!')
        print('This explains why it fails in production but works locally')
        print('The _is_instagram_url() function returns False, so it doesn\'t get Instagram-specific handling')
    else:
        print('✅ Both URLs match the regex - issue is elsewhere')

if __name__ == '__main__':
    test_instagram_regex() 