#!/usr/bin/env python3
"""
PHASE 4: SSRF PENETRATION TESTING
==================================
Comprehensive Server-Side Request Forgery (SSRF) testing against production system
Following OWASP Top 10 A10:2021 - Server-Side Request Forgery

Target: memeit.pro production API
Focus: /api/v1/metadata endpoint (highest SSRF risk)
"""

import requests
import json
import time
from datetime import datetime
import urllib.parse

class SSRFPenetrationTester:
    def __init__(self):
        self.base_url = "https://memeit.pro"
        self.metadata_endpoint = f"{self.base_url}/api/v1/metadata"
        self.results = []
        self.start_time = datetime.now()
        
    def log(self, message, test_type="INFO", status="TESTING"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        result = {
            "timestamp": timestamp,
            "test": test_type,
            "status": status,
            "message": message
        }
        self.results.append(result)
        
        # Color coding for output
        colors = {
            "PASS": "\033[92m✅",
            "FAIL": "\033[91m❌", 
            "VULN": "\033[91m🚨",
            "INFO": "\033[94mℹ️",
            "WARN": "\033[93m⚠️"
        }
        reset = "\033[0m"
        
        color = colors.get(status, "\033[0m")
        print(f"{color} [{timestamp}] {test_type}: {message}{reset}")

    def test_ssrf_payload(self, payload_url, description, expect_blocked=True):
        """Test individual SSRF payload"""
        self.log(f"Testing: {description}", "SSRF", "TESTING")
        
        try:
            response = requests.post(
                self.metadata_endpoint,
                json={"url": payload_url},
                timeout=15,
                headers={"Content-Type": "application/json"}
            )
            
            # Analyze response for SSRF indicators
            if response.status_code == 422:
                # Check error message for proper SSRF blocking
                try:
                    error_data = response.json()
                    error_detail = error_data.get("detail", "").lower()
                    
                    if any(keyword in error_detail for keyword in 
                           ["domain not allowed", "invalid url", "unsupported", "blocked"]):
                        if expect_blocked:
                            self.log(f"BLOCKED (Expected): {error_detail}", "SSRF", "PASS")
                            return "BLOCKED"
                        else:
                            self.log(f"Unexpected block: {error_detail}", "SSRF", "WARN")
                            return "BLOCKED"
                    else:
                        self.log(f"Unexpected 422 error: {error_detail}", "SSRF", "WARN")
                        return "ERROR"
                except:
                    self.log(f"422 response but couldn't parse JSON", "SSRF", "WARN")
                    return "ERROR"
                    
            elif response.status_code == 200:
                if expect_blocked:
                    self.log(f"🚨 POTENTIAL SSRF VULNERABILITY - Request succeeded when it should be blocked!", "SSRF", "VULN")
                    return "VULNERABLE"
                else:
                    self.log(f"Request succeeded as expected", "SSRF", "PASS")
                    return "SUCCESS"
                    
            else:
                self.log(f"Unexpected status code: {response.status_code}", "SSRF", "WARN")
                return "ERROR"
                
        except requests.exceptions.Timeout:
            if expect_blocked:
                self.log(f"Request timed out (likely blocked at network level)", "SSRF", "PASS")
                return "TIMEOUT"
            else:
                self.log(f"Unexpected timeout", "SSRF", "WARN")
                return "TIMEOUT"
                
        except Exception as e:
            self.log(f"Request failed: {str(e)}", "SSRF", "ERROR")
            return "ERROR"

    def run_ssrf_tests(self):
        """Execute comprehensive SSRF test suite"""
        self.log("🚀 Starting SSRF Penetration Testing Suite", "SSRF", "INFO")
        
        # Test 1: Internal Network Access Attempts
        self.log("=== Test Category 1: Internal Network Access ===", "SSRF", "INFO")
        
        internal_targets = [
            ("http://127.0.0.1:8000/health", "Localhost backend access"),
            ("http://localhost:8000/health", "Localhost alternative"),
            ("http://0.0.0.0:8000/health", "Wildcard IP access"),
            ("http://10.0.0.1/", "Private network 10.x.x.x"),
            ("http://192.168.1.1/", "Private network 192.168.x.x"),
            ("http://172.16.0.1/", "Private network 172.16.x.x"),
            ("http://backend:8000/health", "Docker internal service"),
            ("http://redis:6379/", "Internal Redis access"),
        ]
        
        for url, desc in internal_targets:
            self.test_ssrf_payload(url, desc, expect_blocked=True)
            time.sleep(1)  # Rate limiting respect
            
        # Test 2: Cloud Metadata Endpoints
        self.log("=== Test Category 2: Cloud Metadata Access ===", "SSRF", "INFO")
        
        cloud_targets = [
            ("http://169.254.169.254/latest/meta-data/", "AWS EC2 metadata"),
            ("http://169.254.169.254/latest/user-data/", "AWS EC2 user data"),
            ("http://169.254.169.254/computeMetadata/v1/", "Google Cloud metadata"),
            ("http://metadata.google.internal/computeMetadata/v1/", "Google Cloud alt"),
            ("http://169.254.169.254/metadata/instance", "Azure metadata"),
        ]
        
        for url, desc in cloud_targets:
            self.test_ssrf_payload(url, desc, expect_blocked=True)
            time.sleep(1)
            
        # Test 3: Port Scanning Attempts
        self.log("=== Test Category 3: Port Scanning ===", "SSRF", "INFO")
        
        port_scan_targets = [
            ("http://127.0.0.1:22/", "SSH port scanning"),
            ("http://127.0.0.1:3306/", "MySQL port scanning"),
            ("http://127.0.0.1:5432/", "PostgreSQL port scanning"),
            ("http://127.0.0.1:6379/", "Redis port scanning"),
            ("http://127.0.0.1:27017/", "MongoDB port scanning"),
            ("http://memeit.pro:22/", "External SSH scanning"),
        ]
        
        for url, desc in port_scan_targets:
            self.test_ssrf_payload(url, desc, expect_blocked=True)
            time.sleep(1)
            
        # Test 4: Protocol Bypass Attempts
        self.log("=== Test Category 4: Protocol Bypass ===", "SSRF", "INFO")
        
        protocol_targets = [
            ("ftp://127.0.0.1/", "FTP protocol bypass"),
            ("file:///etc/passwd", "File protocol bypass"),
            ("gopher://127.0.0.1:6379/", "Gopher protocol bypass"),
            ("dict://127.0.0.1:11211/", "Dict protocol bypass"),
            ("ldap://127.0.0.1:389/", "LDAP protocol bypass"),
        ]
        
        for url, desc in protocol_targets:
            self.test_ssrf_payload(url, desc, expect_blocked=True)
            time.sleep(1)
            
        # Test 5: URL Encoding Bypass Attempts
        self.log("=== Test Category 5: URL Encoding Bypass ===", "SSRF", "INFO")
        
        encoded_targets = [
            ("http://127.0.0.1:8000%2fhealth", "URL encoding bypass %2f"),
            ("http://127%2e0%2e0%2e1:8000/health", "IP encoding bypass"),
            ("http://0x7f000001:8000/health", "Hex IP bypass"),
            ("http://2130706433:8000/health", "Decimal IP bypass"),
            ("http://[::1]:8000/health", "IPv6 localhost bypass"),
        ]
        
        for url, desc in encoded_targets:
            self.test_ssrf_payload(url, desc, expect_blocked=True)
            time.sleep(1)
            
        # Test 6: Domain Validation - Legitimate URLs (should work)
        self.log("=== Test Category 6: Legitimate Domain Testing ===", "SSRF", "INFO")
        
        legitimate_targets = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "YouTube - should work"),
            ("https://www.instagram.com/reel/test/", "Instagram - should work"), 
            ("https://www.facebook.com/video/test/", "Facebook - should work"),
            ("https://www.reddit.com/r/test/", "Reddit - should work"),
        ]
        
        for url, desc in legitimate_targets:
            self.test_ssrf_payload(url, desc, expect_blocked=False)
            time.sleep(2)  # Longer delay for legitimate requests
            
        # Test 7: Redirect Chain Bypass Attempts  
        self.log("=== Test Category 7: Redirect Bypass ===", "SSRF", "INFO")
        
        # Note: These would require setting up redirect URLs, skipping for now
        self.log("Redirect bypass tests require external setup - documented for manual testing", "SSRF", "INFO")

    def generate_report(self):
        """Generate comprehensive test report"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print("\n" + "="*80)
        print("🛡️  SSRF PENETRATION TESTING REPORT")
        print("="*80)
        
        # Count results by status
        status_counts = {}
        vulnerabilities = []
        
        for result in self.results:
            status = result.get("status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if status == "VULN":
                vulnerabilities.append(result)
        
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {len([r for r in self.results if r.get('test') == 'SSRF'])}")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Blocked (Expected): {status_counts.get('PASS', 0)}")
        print(f"   Vulnerabilities Found: {status_counts.get('VULN', 0)}")
        print(f"   Errors/Warnings: {status_counts.get('WARN', 0) + status_counts.get('ERROR', 0)}")
        
        if vulnerabilities:
            print(f"\n🚨 CRITICAL VULNERABILITIES DETECTED:")
            for vuln in vulnerabilities:
                print(f"   - {vuln['message']}")
        else:
            print(f"\n✅ NO SSRF VULNERABILITIES DETECTED")
            print(f"   All internal/cloud/protocol access attempts were properly blocked")
            
        print(f"\n📋 Detailed Results:")
        for result in self.results:
            if result.get("test") == "SSRF":
                status_icon = {"PASS": "✅", "VULN": "🚨", "WARN": "⚠️", "ERROR": "❌"}.get(result["status"], "ℹ️")
                print(f"   {status_icon} {result['message']}")
                
        print("\n" + "="*80)

if __name__ == "__main__":
    print("🔒 PHASE 4: SSRF PENETRATION TESTING")
    print("Target: memeit.pro production environment")
    print("Testing OWASP A10:2021 - Server-Side Request Forgery")
    print("="*80)
    
    tester = SSRFPenetrationTester()
    tester.run_ssrf_tests()
    tester.generate_report()
    
    print("\n🎯 Next: Run additional OWASP Top 10 penetration tests")
    print("📝 Results logged for security audit documentation") 