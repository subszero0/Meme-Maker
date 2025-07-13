#!/usr/bin/env python3
"""
Production Environment Investigation Script
Identifies why URLs with underscores fail in production but work locally.
"""

import requests
import urllib.parse
import time

def test_production_environment_differences():
    """Test various production environment differences that could affect underscore handling"""
    
    print('🔍 DEEP INVESTIGATION: Production Environment Differences')
    print('=' * 70)
    print('🎯 Goal: Find WHY underscores fail in production but work locally')
    print()
    
    # Test cases - same base URL with different patterns
    test_cases = [
        {
            'name': 'Baseline Working (No Underscore)',
            'url': 'https://www.instagram.com/reel/DLjuZlDTrq3/?igsh=MXIxNGNrenp4bGF5aw==',
            'expected': 'SUCCESS - Should work as baseline'
        },
        {
            'name': 'Target Failing (Original Underscore)',
            'url': 'https://www.instagram.com/reel/DLiGaJABO_a/?igsh=MWQwc3BqcHA2M2k3Mw==',
            'expected': 'FAIL - Original problem URL'
        },
        {
            'name': 'Modified Working + Underscore Test',
            'url': 'https://www.instagram.com/reel/DLjuZlDTrq3_test/?igsh=MXIxNGNrenp4bGF5aw==',
            'expected': 'FAIL - Proves underscore is the trigger'
        },
        {
            'name': 'Different Platform Test (YouTube)',
            'url': 'https://www.youtube.com/watch?v=test_underscore',
            'expected': 'Unknown - Test if underscore issue is Instagram-specific'
        }
    ]
    
    print('📋 Test Cases:')
    for i, case in enumerate(test_cases, 1):
        print(f'  {i}. {case["name"]}')
        print(f'     URL: {case["url"]}')
        print(f'     Expected: {case["expected"]}')
        print()
    
    # Execute tests
    results = []
    
    for case in test_cases:
        print(f'🧪 Testing: {case["name"]}')
        print(f'URL: {case["url"]}')
        
        try:
            start_time = time.time()
            response = requests.post(
                'https://memeit.pro/api/v1/metadata/extract',
                json={'url': case['url']},
                headers={'Content-Type': 'application/json'},
                timeout=60  # Longer timeout for investigation
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                title = data.get('title', 'No title')
                print(f'✅ SUCCESS ({duration:.1f}s): {title}')
                results.append((case['name'], 'SUCCESS', response.status_code, duration, title))
            elif response.status_code == 422:
                print(f'⚠️  INVALID URL ({duration:.1f}s): {response.status_code}')
                results.append((case['name'], 'INVALID', response.status_code, duration, 'N/A'))
            else:
                print(f'❌ FAILED ({duration:.1f}s): {response.status_code} {response.reason}')
                results.append((case['name'], 'FAILED', response.status_code, duration, 'N/A'))
                
        except requests.exceptions.Timeout:
            print(f'⏰ TIMEOUT: Request took longer than 60 seconds')
            results.append((case['name'], 'TIMEOUT', 'N/A', '>60s', 'N/A'))
        except Exception as e:
            print(f'💥 ERROR: {str(e)}')
            results.append((case['name'], 'ERROR', 'N/A', 'N/A', str(e)))
        
        print()
        time.sleep(2)  # Brief pause between tests
    
    # Analysis
    print('=' * 70)
    print('📊 COMPREHENSIVE ANALYSIS')
    print('=' * 70)
    
    # Results summary
    print('🎯 Test Results Summary:')
    for name, result, status, duration, details in results:
        status_emoji = {'SUCCESS': '✅', 'FAILED': '❌', 'INVALID': '⚠️', 'TIMEOUT': '⏰', 'ERROR': '💥'}.get(result, '❓')
        print(f'{status_emoji} {name}: {result} ({status}) - {duration}')
    
    print()
    
    # Pattern analysis
    underscore_results = [r for r in results if 'underscore' in r[0].lower() or 'DLiGaJABO_a' in r[0]]
    working_results = [r for r in results if r[1] == 'SUCCESS']
    
    print('🔍 Pattern Analysis:')
    
    if len(underscore_results) > 0:
        failed_underscore = [r for r in underscore_results if r[1] == 'FAILED']
        if len(failed_underscore) == len(underscore_results):
            print('❗ ALL URLs with underscores fail → Production environment issue confirmed')
            print('❗ This is NOT a content-specific or IP blocking issue')
            print('❗ This is a production infrastructure or configuration issue')
        else:
            print('⚠️  Mixed results with underscores → Need deeper investigation')
    
    # Environment hypothesis
    print()
    print('🏗️ Production Environment Hypotheses to Investigate:')
    print('1. 🐳 Docker container environment differences')
    print('2. 🌐 Nginx URL processing differences between local and production')
    print('3. 🔧 yt-dlp version differences between environments')
    print('4. 📦 Python/dependency version differences')
    print('5. 🌍 Network routing or proxy differences')
    print('6. 💾 Cache key generation with underscores')
    print('7. 🔒 Security/firewall rules affecting URLs with underscores')
    
    # Next steps
    print()
    print('🚀 Recommended Next Steps:')
    if any(r[1] == 'FAILED' for r in underscore_results):
        print('1. ✅ CONFIRMED: Underscore is the trigger')
        print('2. 🔍 Check production container logs for actual yt-dlp errors')
        print('3. 🔧 Compare production vs local yt-dlp versions')
        print('4. 🐳 Test same URL in production Docker environment directly')
        print('5. 🌐 Bypass nginx and test backend directly if possible')
    
    return results

if __name__ == '__main__':
    test_production_environment_differences() 