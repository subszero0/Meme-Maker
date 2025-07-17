#!/usr/bin/env python3
"""
Job Analysis Script - Follow up to T-001 testing
Purpose: Analyze what happens to jobs with malicious payloads
"""

import requests
import json
import time

SECURITY_TEST_BASE_URL = "http://localhost:8001"

def test_malicious_job_processing():
    """Test a specific malicious payload and track its processing"""
    print("🔍 Testing malicious job processing...")
    
    # Submit a job with command injection payload
    malicious_payload = "https://example.com/video.mp4; echo 'INJECTION_TEST_MARKER' > /tmp/injection_test"
    
    data = {
        "url": malicious_payload,
        "in_ts": 0,
        "out_ts": 10
    }
    
    response = requests.post(f"{SECURITY_TEST_BASE_URL}/api/v1/jobs", json=data)
    print(f"📤 Job submission response: {response.status_code}")
    
    if response.status_code == 201:
        job_data = response.json()
        job_id = job_data.get("id")
        print(f"📋 Job ID: {job_id}")
        
        # Monitor job status
        for i in range(10):  # Check for 10 seconds
            try:
                status_response = requests.get(f"{SECURITY_TEST_BASE_URL}/api/v1/jobs/{job_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get("status")
                    print(f"⏱️ Job status ({i+1}s): {status}")
                    
                    if status in ["completed", "failed"]:
                        print(f"🏁 Final status: {status}")
                        if "error" in status_data:
                            print(f"❌ Error: {status_data['error']}")
                        break
                        
                time.sleep(1)
            except Exception as e:
                print(f"⚠️ Error checking status: {e}")
                break

def test_legitimate_job():
    """Test a legitimate job for comparison"""
    print("\n🔍 Testing legitimate job for comparison...")
    
    legitimate_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Safe test video
    
    data = {
        "url": legitimate_url,
        "in_ts": 0,
        "out_ts": 10
    }
    
    response = requests.post(f"{SECURITY_TEST_BASE_URL}/api/v1/jobs", json=data)
    print(f"📤 Legitimate job response: {response.status_code}")
    
    if response.status_code == 201:
        job_data = response.json()
        job_id = job_data.get("id")
        print(f"📋 Legitimate Job ID: {job_id}")

def check_container_for_injection_evidence():
    """Check if there's any evidence of command injection in the worker container"""
    print("\n🔍 Checking container for injection evidence...")
    
    # This would ideally check container logs, but we'll implement a simple approach
    # In a real security test, you'd inspect container filesystem, logs, etc.
    
    print("ℹ️ Note: In a comprehensive test, we would:")
    print("   1. Inspect worker container filesystem for injection artifacts")
    print("   2. Check container logs for suspicious command execution")
    print("   3. Monitor container resource usage during job processing")
    print("   4. Verify container isolation effectiveness")

if __name__ == "__main__":
    print("🔍 Job Analysis - Follow-up to T-001 Command Injection Testing")
    print("=" * 60)
    
    test_malicious_job_processing()
    test_legitimate_job()
    check_container_for_injection_evidence()
    
    print("\n📊 ANALYSIS SUMMARY:")
    print("Status 201 indicates job was accepted and queued")
    print("Need to verify:")
    print("  ✓ Jobs fail during processing (not at injection point)")
    print("  ✓ yt-dlp properly sanitizes/validates URLs")
    print("  ✓ Container isolation prevents actual command execution")
    print("  ✓ No files created from injection attempts") 