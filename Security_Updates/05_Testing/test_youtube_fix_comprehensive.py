#!/usr/bin/env python3
"""
Comprehensive test for YouTube bot detection fixes

Tests multiple scenarios to validate the improved yt-dlp configuration.
"""

import requests
import json
import time
import sys
from datetime import datetime

# Test URLs for different scenarios
TEST_URLS = [
    {
        'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'description': 'Classic YouTube video (Rick Roll)',
        'expected': 'success_or_specific_error'
    },
    {
        'url': 'https://www.youtube.com/watch?v=wgSQ5Uevegg',
        'description': 'URL from user screenshot',
        'expected': 'success_or_specific_error'
    },
    {
        'url': 'https://www.youtube.com/watch?v=jNQXAC9IVRw',
        'description': 'Another popular video',
        'expected': 'success_or_specific_error'
    }
]

def test_single_url(url_data):
    """Test a single URL and analyze the response"""
    print(f"\n{'='*60}")
    print(f"Testing: {url_data['description']}")
    print(f"URL: {url_data['url']}")
    print(f"{'='*60}")
    
    api_url = "https://memeit.pro/api/v1/metadata"
    payload = {"url": url_data['url']}
    
    start_time = time.time()
    
    try:
        response = requests.post(
            api_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=45  # Increased timeout for bot detection handling
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️  Response time: {duration:.2f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Success case
            data = response.json()
            print(f"✅ SUCCESS!")
            print(f"   Title: {data.get('title', 'N/A')}")
            print(f"   Duration: {data.get('duration', 0)} seconds")
            print(f"   Resolutions: {data.get('resolutions', [])}")
            if data.get('thumbnail_url'):
                print(f"   Thumbnail: Available")
            return {
                'status': 'success',
                'title': data.get('title'),
                'duration': duration,
                'response_time': duration
            }
            
        elif response.status_code == 400:
            # Expected error case - analyze the error
            try:
                error_data = response.json()
                error_detail = error_data.get('detail', 'Unknown error')
                
                print(f"⚠️  Expected Error (400):")
                print(f"   {error_detail}")
                
                # Analyze error type
                if 'Sign in to confirm' in error_detail:
                    print(f"🤖 Bot detection triggered - this is expected")
                    print(f"   The improved configuration should reduce this over time")
                    return {
                        'status': 'bot_detection',
                        'error': error_detail,
                        'response_time': duration
                    }
                elif 'Private video' in error_detail or 'unavailable' in error_detail:
                    print(f"🔒 Video access issue - not a bot detection problem")
                    return {
                        'status': 'video_unavailable',
                        'error': error_detail,
                        'response_time': duration
                    }
                else:
                    print(f"❓ Other error - needs investigation")
                    return {
                        'status': 'other_error',
                        'error': error_detail,
                        'response_time': duration
                    }
                    
            except json.JSONDecodeError:
                print(f"❌ Could not parse error response")
                print(f"   Raw response: {response.text}")
                return {
                    'status': 'parse_error',
                    'response_time': duration
                }
                
        else:
            # Unexpected status code
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return {
                'status': 'unexpected_status',
                'status_code': response.status_code,
                'response_time': duration
            }
            
    except requests.exceptions.Timeout:
        print(f"⏰ Request timed out (45s)")
        return {
            'status': 'timeout',
            'response_time': 45
        }
        
    except requests.exceptions.RequestException as e:
        print(f"🌐 Network error: {e}")
        return {
            'status': 'network_error',
            'error': str(e)
        }

def analyze_results(results):
    """Analyze the test results and provide insights"""
    print(f"\n{'='*60}")
    print("📊 TEST RESULTS ANALYSIS")
    print(f"{'='*60}")
    
    total_tests = len(results)
    success_count = sum(1 for r in results if r['status'] == 'success')
    bot_detection_count = sum(1 for r in results if r['status'] == 'bot_detection')
    other_errors = total_tests - success_count - bot_detection_count
    
    print(f"📈 Summary:")
    print(f"   Total tests: {total_tests}")
    print(f"   Successful: {success_count}")
    print(f"   Bot detection: {bot_detection_count}")
    print(f"   Other errors: {other_errors}")
    
    if success_count > 0:
        print(f"✅ Success rate: {(success_count/total_tests)*100:.1f}%")
        avg_response_time = sum(r['response_time'] for r in results if r['status'] == 'success') / success_count
        print(f"⏱️  Average response time for successful requests: {avg_response_time:.2f}s")
    
    if bot_detection_count > 0:
        print(f"🤖 Bot detection rate: {(bot_detection_count/total_tests)*100:.1f}%")
        print(f"   This is expected and should improve over time with the new configuration")
    
    print(f"\n📋 Recommendations:")
    
    if success_count == total_tests:
        print("🎉 All tests passed! The fix is working perfectly.")
    elif success_count > 0:
        print("✅ Partial success - the fix is working for some videos.")
        print("   This is normal as YouTube's bot detection varies by video and time.")
    elif bot_detection_count == total_tests:
        print("⚠️  All requests triggered bot detection.")
        print("   This may be temporary. Try again in a few minutes.")
        print("   The improved configuration should help reduce this over time.")
    else:
        print("🔍 Mixed results - review individual test outputs above.")
    
    return {
        'success_rate': (success_count/total_tests)*100,
        'bot_detection_rate': (bot_detection_count/total_tests)*100,
        'total_tests': total_tests
    }

def main():
    print("🧪 Comprehensive YouTube Bot Detection Fix Test")
    print(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Testing {len(TEST_URLS)} different YouTube URLs")
    
    results = []
    
    for i, url_data in enumerate(TEST_URLS, 1):
        print(f"\n🔄 Test {i}/{len(TEST_URLS)}")
        result = test_single_url(url_data)
        result['url'] = url_data['url']
        result['description'] = url_data['description']
        results.append(result)
        
        # Add delay between requests to be respectful
        if i < len(TEST_URLS):
            print("⏳ Waiting 3 seconds before next test...")
            time.sleep(3)
    
    # Analyze results
    summary = analyze_results(results)
    
    # Save results to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"youtube_fix_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': summary,
            'detailed_results': results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    print(f"✅ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 