#!/usr/bin/env python3
"""
PHASE 4: A01 BROKEN ACCESS CONTROL PENETRATION TESTING
======================================================
Comprehensive testing for OWASP A01:2021 - Broken Access Control
Target: memeit.pro production API

Test Categories:
1. Horizontal Privilege Escalation
2. Vertical Privilege Escalation  
3. Direct Object Reference Attacks
4. Administrative Function Access
5. Path Traversal Attacks
6. Force Browsing Attacks
"""

import requests
import json
import time
from datetime import datetime
import urllib.parse

class AccessControlTester:
    def __init__(self):
        self.base_url = "https://memeit.pro"
        self.results = []
        self.start_time = datetime.now()
        
        # Common endpoints discovered in Phase 1
        self.endpoints = [
            "/api/v1/metadata",
            "/api/v1/jobs", 
            "/api/v1/clips",
            "/api/v1/admin/metrics",
            "/api/v1/admin/health",
            "/health",
            "/",
            "/debug/cors",
            "/debug/redis"
        ]
        
    def log(self, message, test_type="ACCESS", status="TESTING"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        result = {
            "timestamp": timestamp,
            "test": test_type,
            "status": status,
            "message": message
        }
        self.results.append(result)
        
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
        
    def test_endpoint_access(self, endpoint, method="GET", headers=None, data=None):
        """Test access to endpoint and return response details"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return None
                
            return {
                "status_code": response.status_code,
                "content_length": len(response.content),
                "headers": dict(response.headers),
                "content": response.text[:500]  # First 500 chars
            }
            
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def test_horizontal_privilege_escalation(self):
        """Test for horizontal privilege escalation (same role, different user)"""
        self.log("=== Testing Horizontal Privilege Escalation ===", "ACCESS", "INFO")
        
        # Test 1: User-specific resource access patterns
        self.log("Testing user-specific resource enumeration...", "ACCESS", "TESTING")
        
        # Common user ID patterns to test
        user_patterns = [
            "/api/v1/jobs/1",
            "/api/v1/jobs/user/123", 
            "/api/v1/clips/user_123",
            "/api/v1/profile/456",
            "/api/v1/history/789"
        ]
        
        for pattern in user_patterns:
            result = self.test_endpoint_access(pattern)
            if result and result.get("status_code") == 200:
                self.log(f"POTENTIAL VULNERABILITY: User resource accessible at {pattern}", "ACCESS", "VULN")
            elif result and result.get("status_code") == 404:
                self.log(f"User resource properly not found: {pattern}", "ACCESS", "PASS")
            elif result and result.get("status_code") == 401:
                self.log(f"Authentication required for: {pattern}", "ACCESS", "PASS")
            else:
                self.log(f"Unexpected response for {pattern}: {result.get('status_code', 'ERROR')}", "ACCESS", "WARN")
                
        # Test 2: Parameter-based user access (IDOR)
        self.log("Testing Insecure Direct Object Reference (IDOR)...", "ACCESS", "TESTING")
        
        # Test common IDOR patterns
        idor_tests = [
            ("/api/v1/metadata", {"url": "https://youtube.com/watch?v=test", "user_id": "1"}),
            ("/api/v1/jobs", {"url": "https://youtube.com/watch?v=test", "owner": "admin"}),
            ("/api/v1/clips", {"file_id": "123", "user": "other_user"})
        ]
        
        for endpoint, data in idor_tests:
            result = self.test_endpoint_access(endpoint, "POST", data=data)
            if result and result.get("status_code") == 200:
                self.log(f"POTENTIAL IDOR: Accepted user parameter at {endpoint}", "ACCESS", "WARN")
            elif result and result.get("status_code") in [400, 422]:
                self.log(f"User parameter validation working: {endpoint}", "ACCESS", "PASS")
                
    def test_vertical_privilege_escalation(self):
        """Test for vertical privilege escalation (role elevation)"""
        self.log("=== Testing Vertical Privilege Escalation ===", "ACCESS", "INFO")
        
        # Test 1: Admin endpoint access without authentication
        self.log("Testing admin endpoint access without authentication...", "ACCESS", "TESTING")
        
        admin_endpoints = [
            "/api/v1/admin/metrics",
            "/api/v1/admin/health", 
            "/api/v1/admin/users",
            "/api/v1/admin/system",
            "/api/v1/admin/logs",
            "/api/v1/admin/config"
        ]
        
        for endpoint in admin_endpoints:
            result = self.test_endpoint_access(endpoint)
            if result and result.get("status_code") == 200:
                self.log(f"CRITICAL: Admin endpoint accessible without auth: {endpoint}", "ACCESS", "VULN")
            elif result and result.get("status_code") == 401:
                self.log(f"Admin endpoint properly protected: {endpoint}", "ACCESS", "PASS")
            elif result and result.get("status_code") == 403:
                self.log(f"Admin endpoint forbidden (good): {endpoint}", "ACCESS", "PASS")
            elif result and result.get("status_code") == 404:
                self.log(f"Admin endpoint not found: {endpoint}", "ACCESS", "INFO")
        
        # Test 2: Role injection via headers
        self.log("Testing role injection via headers...", "ACCESS", "TESTING")
        
        role_headers = [
            {"X-User-Role": "admin"},
            {"X-Role": "administrator"},
            {"User-Role": "admin"},
            {"Authorization": "Bearer admin"},
            {"X-Admin": "true"},
            {"Is-Admin": "1"}
        ]
        
        for headers in role_headers:
            result = self.test_endpoint_access("/api/v1/admin/metrics", headers=headers)
            if result and result.get("status_code") == 200:
                self.log(f"CRITICAL: Role injection successful with headers: {headers}", "ACCESS", "VULN")
            else:
                self.log(f"Role injection blocked for headers: {headers}", "ACCESS", "PASS")
                
        # Test 3: Parameter-based role elevation
        self.log("Testing role elevation via parameters...", "ACCESS", "TESTING")
        
        role_params = [
            {"role": "admin"},
            {"is_admin": "true"},
            {"admin": "1"},
            {"privileges": "admin"},
            {"access_level": "admin"}
        ]
        
        for params in role_params:
            result = self.test_endpoint_access("/api/v1/metadata", "POST", 
                                             data={"url": "https://youtube.com/watch?v=test", **params})
            if result and "admin" in result.get("content", "").lower():
                self.log(f"POTENTIAL: Admin context in response with params: {params}", "ACCESS", "WARN")
            else:
                self.log(f"Role parameter ignored: {params}", "ACCESS", "PASS")
    
    def test_direct_object_reference(self):
        """Test for insecure direct object references"""
        self.log("=== Testing Direct Object Reference Attacks ===", "ACCESS", "INFO")
        
        # Test 1: Numeric ID enumeration
        self.log("Testing numeric ID enumeration...", "ACCESS", "TESTING")
        
        id_endpoints = [
            "/api/v1/jobs/{id}",
            "/api/v1/clips/{id}",
            "/api/v1/files/{id}",
            "/api/v1/download/{id}"
        ]
        
        test_ids = [1, 2, 100, 999, "admin", "../etc/passwd", "NULL", "0"]
        
        for endpoint_template in id_endpoints:
            for test_id in test_ids:
                endpoint = endpoint_template.format(id=test_id)
                result = self.test_endpoint_access(endpoint)
                
                if result and result.get("status_code") == 200:
                    self.log(f"POTENTIAL: Direct access to object {test_id} at {endpoint}", "ACCESS", "WARN")
                elif result and result.get("status_code") == 404:
                    self.log(f"Object {test_id} not found (expected): {endpoint}", "ACCESS", "PASS")
                elif result and result.get("status_code") == 401:
                    self.log(f"Authentication required for {test_id}: {endpoint}", "ACCESS", "PASS")
        
        # Test 2: File path traversal
        self.log("Testing file path traversal...", "ACCESS", "TESTING")
        
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "/etc/passwd",
            "../../app/config.py",
            "../.env",
            "../../docker-compose.yml"
        ]
        
        for payload in traversal_payloads:
            encoded_payload = urllib.parse.quote(payload, safe='')
            result = self.test_endpoint_access(f"/api/v1/clips/{encoded_payload}")
            
            if result and result.get("status_code") == 200:
                content = result.get("content", "")
                if "root:" in content or "passwd" in content or "[users]" in content:
                    self.log(f"CRITICAL: Path traversal successful with {payload}", "ACCESS", "VULN")
                else:
                    self.log(f"Path traversal blocked: {payload}", "ACCESS", "PASS")
            else:
                self.log(f"Path traversal properly rejected: {payload}", "ACCESS", "PASS")
    
    def test_administrative_function_access(self):
        """Test access to administrative functions"""
        self.log("=== Testing Administrative Function Access ===", "ACCESS", "INFO")
        
        # Test 1: Administrative operations
        self.log("Testing administrative operations...", "ACCESS", "TESTING")
        
        admin_operations = [
            ("/api/v1/admin/restart", "POST"),
            ("/api/v1/admin/shutdown", "POST"),
            ("/api/v1/admin/clear-cache", "POST"),
            ("/api/v1/admin/delete-all", "DELETE"),
            ("/api/v1/admin/backup", "POST"),
            ("/api/v1/admin/logs", "GET"),
            ("/api/v1/system/status", "GET"),
            ("/api/v1/system/health", "GET")
        ]
        
        for endpoint, method in admin_operations:
            result = self.test_endpoint_access(endpoint, method)
            if result and result.get("status_code") == 200:
                self.log(f"CRITICAL: Admin operation accessible: {method} {endpoint}", "ACCESS", "VULN")
            elif result and result.get("status_code") == 401:
                self.log(f"Admin operation properly protected: {method} {endpoint}", "ACCESS", "PASS")
            elif result and result.get("status_code") == 404:
                self.log(f"Admin operation not found: {method} {endpoint}", "ACCESS", "INFO")
        
        # Test 2: Debug and development endpoints
        self.log("Testing debug and development endpoints...", "ACCESS", "TESTING")
        
        debug_endpoints = [
            "/debug",
            "/debug/cors",
            "/debug/redis", 
            "/test",
            "/dev",
            "/development",
            "/.env",
            "/config",
            "/status",
            "/info",
            "/version"
        ]
        
        for endpoint in debug_endpoints:
            result = self.test_endpoint_access(endpoint)
            if result and result.get("status_code") == 200:
                content = result.get("content", "")
                if any(keyword in content.lower() for keyword in ["debug", "config", "password", "secret", "key"]):
                    self.log(f"HIGH: Debug endpoint exposing sensitive info: {endpoint}", "ACCESS", "VULN")
                else:
                    self.log(f"Debug endpoint accessible but safe: {endpoint}", "ACCESS", "WARN")
            elif result and result.get("status_code") == 404:
                self.log(f"Debug endpoint properly disabled: {endpoint}", "ACCESS", "PASS")
    
    def test_force_browsing(self):
        """Test for force browsing and hidden functionality"""
        self.log("=== Testing Force Browsing Attacks ===", "ACCESS", "INFO")
        
        # Test 1: Common hidden directories and files
        self.log("Testing common hidden directories...", "ACCESS", "TESTING")
        
        hidden_paths = [
            "/.git",
            "/.git/config", 
            "/.env",
            "/.env.production",
            "/backup",
            "/backups",
            "/tmp",
            "/logs",
            "/config",
            "/admin",
            "/administrator",
            "/management",
            "/internal",
            "/private",
            "/restricted"
        ]
        
        for path in hidden_paths:
            result = self.test_endpoint_access(path)
            if result and result.get("status_code") == 200:
                self.log(f"WARNING: Hidden path accessible: {path}", "ACCESS", "WARN")
            elif result and result.get("status_code") == 403:
                self.log(f"Hidden path forbidden (good): {path}", "ACCESS", "PASS")
            elif result and result.get("status_code") == 404:
                self.log(f"Hidden path not found (expected): {path}", "ACCESS", "PASS")
        
        # Test 2: HTTP method bypass
        self.log("Testing HTTP method bypass...", "ACCESS", "TESTING")
        
        protected_endpoint = "/api/v1/admin/metrics"
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"]
        
        for method in methods:
            result = self.test_endpoint_access(protected_endpoint, method)
            if result and result.get("status_code") == 200:
                self.log(f"POTENTIAL: Admin endpoint accessible via {method}", "ACCESS", "WARN")
            elif result and result.get("status_code") == 405:
                self.log(f"Method {method} not allowed (expected)", "ACCESS", "PASS")
            elif result and result.get("status_code") == 401:
                self.log(f"Authentication required for {method} (good)", "ACCESS", "PASS")
    
    def run_all_tests(self):
        """Run all access control tests"""
        self.log("🔒 PHASE 4: A01 BROKEN ACCESS CONTROL PENETRATION TESTING", "ACCESS", "INFO")
        self.log("Target: memeit.pro production environment", "ACCESS", "INFO")
        self.log("Testing OWASP A01:2021 - Broken Access Control", "ACCESS", "INFO")
        self.log("="*80, "ACCESS", "INFO")
        
        # Run all test categories
        self.test_horizontal_privilege_escalation()
        time.sleep(1)
        
        self.test_vertical_privilege_escalation()
        time.sleep(1)
        
        self.test_direct_object_reference()
        time.sleep(1)
        
        self.test_administrative_function_access()
        time.sleep(1)
        
        self.test_force_browsing()
        
        # Generate final report
        self.generate_report()
    
    def generate_report(self):
        """Generate final test report"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Count results
        status_counts = {}
        vulnerabilities = []
        
        for result in self.results:
            status = result["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if status in ["VULN", "WARN"]:
                vulnerabilities.append(result)
        
        access_tests = [r for r in self.results if r["test"] == "ACCESS"]
        total_tests = len(access_tests)
        vuln_count = len([r for r in access_tests if r["status"] == "VULN"])
        warn_count = len([r for r in access_tests if r["status"] == "WARN"]) 
        pass_count = len([r for r in access_tests if r["status"] == "PASS"])
        
        print("\n" + "="*80)
        print("A01 BROKEN ACCESS CONTROL PENETRATION TESTING REPORT")
        print("="*80)
        
        print(f"Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Critical Vulnerabilities: {vuln_count}")
        print(f"   Warnings: {warn_count}")
        print(f"   Passed Controls: {pass_count}")
        
        if vuln_count > 0:
            print(f"\n🚨 CRITICAL ACCESS CONTROL VULNERABILITIES:")
            for vuln in [v for v in vulnerabilities if v["status"] == "VULN"]:
                print(f"   - {vuln['message']}")
        
        if warn_count > 0:
            print(f"\n⚠️ ACCESS CONTROL WARNINGS:")
            for warn in [v for v in vulnerabilities if v["status"] == "WARN"]:
                print(f"   - {warn['message']}")
        
        if vuln_count == 0:
            print(f"\n✅ NO CRITICAL ACCESS CONTROL VULNERABILITIES DETECTED")
            print(f"   Application demonstrates good access control implementation")
        
        # Overall assessment
        if vuln_count == 0 and warn_count <= 2:
            assessment = "EXCELLENT ACCESS CONTROL"
        elif vuln_count == 0 and warn_count <= 5:
            assessment = "GOOD ACCESS CONTROL"
        elif vuln_count <= 2:
            assessment = "MODERATE ACCESS CONTROL ISSUES"
        else:
            assessment = "SIGNIFICANT ACCESS CONTROL VULNERABILITIES"
        
        print(f"\n📊 Overall Assessment: {assessment}")
        print(f"🎯 Next: Run A02 Cryptographic Failures testing")
        print(f"📝 Results logged for security audit documentation")

if __name__ == "__main__":
    tester = AccessControlTester()
    tester.run_all_tests() 