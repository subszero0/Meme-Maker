#!/usr/bin/env python3

import requests
import urllib.parse

def test_url_encoding_scenarios():
    """Test different URL encoding scenarios to find where underscores fail"""
    
    print('🔍 Testing URL Encoding Scenarios in Production')
    print('=' * 60)
    
    # Base URLs
    working_id = 'DLjuZlDTrq3'
    failing_id = 'DLiGaJABO_a'
    
    # Test scenarios
    scenarios = [
        {
            'name': 'Normal Underscore',
            'url': f'https://www.instagram.com/reel/{failing_id}/?igsh=MWQwc3BqcHA2M2k3Mw==',
            'expected': 'Should fail (original behavior)'
        },
        {
            'name': 'URL Encoded Underscore (%5F)',
            'url': f'https://www.instagram.com/reel/DLiGaJABO%5Fa/?igsh=MWQwc3BqcHA2M2k3Mw==',
            'expected': 'Should fail if nginx encoding issue'
        },
        {
            'name': 'Double URL Encoded (%255F)',
            'url': f'https://www.instagram.com/reel/DLiGaJABO%255Fa/?igsh=MWQwc3BqcHA2M2k3Mw==',
            'expected': 'May work if double encoding issue'
        },
        {
            'name': 'Working URL for comparison',
            'url': f'https://www.instagram.com/reel/{working_id}/?igsh=MXIxNGNrenp4bGF5aw==',
            'expected': 'Should work (baseline)'
        }
    ]
    
    results = []
    
    for scenario in scenarios:
        print(f"\n🧪 Testing: {scenario['name']}")
        print(f"URL: {scenario['url']}")
        print(f"Expected: {scenario['expected']}")
        
        try:
            response = requests.post(
                'https://memeit.pro/api/v1/metadata/extract',
                json={'url': scenario['url']},
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS: {data.get('title', 'No title')}")
                results.append((scenario['name'], 'SUCCESS', response.status_code))
            else:
                print(f"❌ FAILED: {response.status_code} {response.reason}")
                results.append((scenario['name'], 'FAILED', response.status_code))
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            results.append((scenario['name'], 'ERROR', str(e)))
    
    # Summary
    print('\n' + '=' * 60)
    print('📊 SUMMARY OF URL ENCODING TESTS')
    print('=' * 60)
    
    for name, result, details in results:
        status_emoji = '✅' if result == 'SUCCESS' else '❌'
        print(f"{status_emoji} {name}: {result} ({details})")
    
    # Analysis
    print('\n🔍 ANALYSIS:')
    underscore_tests = [r for r in results if 'Underscore' in r[0]]
    working_tests = [r for r in results if 'Working' in r[0]]
    
    if any(r[1] == 'SUCCESS' for r in underscore_tests):
        print('- At least one underscore variant works → Encoding issue confirmed')
        print('- Solution: Use the working encoding format')
    elif all(r[1] == 'FAILED' for r in underscore_tests):
        print('- All underscore variants fail → Deeper production issue')
        print('- Need to investigate backend processing or environment differences')
    
    return results

if __name__ == '__main__':
    test_url_encoding_scenarios() 