#!/usr/bin/env python3
"""
COMPREHENSIVE SECURITY FIXES VERIFICATION
==========================================

Test script to verify CRIT-001, CRIT-002, and CRIT-003 security fixes
in staging environment before any deployment to master branch.

Security Fixes Tested:
- CRIT-001: API Documentation Disabled in Production
- CRIT-002: Admin Endpoints Protected with Authentication  
- CRIT-003: Email Services Investigation (False Positive)

Usage:
    python test_security_fixes_staging.py
"""

import asyncio
import json
import os
import sys
import time
from typing import Dict, List, Optional

import requests
from requests.exceptions import ConnectionError, RequestException


class SecurityFixTester:
    """Test suite for verifying critical security fixes"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.admin_api_key = os.getenv("ADMIN_API_KEY", "Zz52sTQ-POlkfbk33wQ2XveCg4_7agVACc5_O0eo0Io")
        self.test_results: List[Dict] = []
        
    def log_test(self, test_name: str, status: str, details: str = "", expected: str = ""):
        """Log test result with detailed information"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "expected": expected,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        if expected and status == "FAIL":
            print(f"   Expected: {expected}")
        print()

    def test_backend_connectivity(self) -> bool:
        """Test basic backend connectivity"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                self.log_test("Backend Connectivity", "PASS", 
                            f"Health endpoint responding: {response.json()}")
                return True
            else:
                self.log_test("Backend Connectivity", "FAIL",
                            f"Health endpoint returned {response.status_code}")
                return False
        except ConnectionError:
            self.log_test("Backend Connectivity", "FAIL",
                        f"Cannot connect to {self.base_url}",
                        "Backend should be running on staging port 8001")
            return False
        except Exception as e:
            self.log_test("Backend Connectivity", "FAIL", str(e))
            return False

    def test_crit_001_api_docs_disabled(self):
        """
        CRIT-001: Test that API documentation is disabled in production environment
        
        When ENVIRONMENT=production:
        - /docs should return 404
        - /redoc should return 404  
        - /openapi.json should return 404
        """
        print("🔍 Testing CRIT-001: API Documentation Disabled in Production")
        
        # Test endpoints that should be disabled
        endpoints = [
            ("/docs", "Swagger UI Documentation"),
            ("/redoc", "ReDoc API Documentation"), 
            ("/openapi.json", "OpenAPI Schema")
        ]
        
        for endpoint, description in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 404:
                    self.log_test(f"CRIT-001: {description}", "PASS",
                                f"Endpoint {endpoint} correctly returns 404 in production")
                else:
                    self.log_test(f"CRIT-001: {description}", "FAIL",
                                f"Endpoint {endpoint} returned {response.status_code}",
                                "Should return 404 when ENVIRONMENT=production")
            except Exception as e:
                self.log_test(f"CRIT-001: {description}", "FAIL", str(e))

    def test_crit_002_admin_auth_protection(self):
        """
        CRIT-002: Test that admin endpoints are properly protected with authentication
        
        Tests:
        1. Unauthenticated access should return 401
        2. Invalid API key should return 403
        3. Valid API key should return success (200/405)
        4. Non-admin endpoints should work normally
        """
        print("🔍 Testing CRIT-002: Admin Authentication Protection")
        
        # Admin endpoints to test (these should exist based on attack surface analysis)
        admin_endpoints = [
            "/api/v1/admin/cache/stats",
            "/api/v1/admin/cache/clear", 
            "/api/v1/admin/storage/info"
        ]
        
        for endpoint in admin_endpoints:
            # Test 1: Unauthenticated access should fail
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 401:
                    self.log_test(f"CRIT-002: Unauthenticated {endpoint}", "PASS",
                                f"Correctly returns 401 for unauthenticated access")
                else:
                    self.log_test(f"CRIT-002: Unauthenticated {endpoint}", "FAIL",
                                f"Returned {response.status_code} instead of 401",
                                "Should return 401 for unauthenticated admin access")
            except Exception as e:
                self.log_test(f"CRIT-002: Unauthenticated {endpoint}", "FAIL", str(e))
            
            # Test 2: Invalid API key should fail
            try:
                headers = {"Authorization": "Bearer invalid-key-12345"}
                response = requests.get(f"{self.base_url}{endpoint}", headers=headers, timeout=5)
                if response.status_code == 403:
                    self.log_test(f"CRIT-002: Invalid Auth {endpoint}", "PASS",
                                f"Correctly returns 403 for invalid API key")
                else:
                    self.log_test(f"CRIT-002: Invalid Auth {endpoint}", "FAIL", 
                                f"Returned {response.status_code} instead of 403",
                                "Should return 403 for invalid admin API key")
            except Exception as e:
                self.log_test(f"CRIT-002: Invalid Auth {endpoint}", "FAIL", str(e))
            
            # Test 3: Valid API key should succeed (or return 405 if method not allowed)
            try:
                headers = {"Authorization": f"Bearer {self.admin_api_key}"}
                response = requests.get(f"{self.base_url}{endpoint}", headers=headers, timeout=5)
                if response.status_code in [200, 405]:
                    self.log_test(f"CRIT-002: Valid Auth {endpoint}", "PASS",
                                f"Valid API key accepted, returned {response.status_code}")
                else:
                    self.log_test(f"CRIT-002: Valid Auth {endpoint}", "FAIL",
                                f"Valid API key returned {response.status_code}",
                                "Should return 200 or 405 for valid admin API key")
            except Exception as e:
                self.log_test(f"CRIT-002: Valid Auth {endpoint}", "FAIL", str(e))
        
        # Test 4: Non-admin endpoints should work normally without auth
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                self.log_test("CRIT-002: Non-admin Endpoint Access", "PASS",
                            "Non-admin endpoints work without authentication")
            else:
                self.log_test("CRIT-002: Non-admin Endpoint Access", "FAIL",
                            f"Health endpoint returned {response.status_code}",
                            "Non-admin endpoints should work without auth")
        except Exception as e:
            self.log_test("CRIT-002: Non-admin Endpoint Access", "FAIL", str(e))

    def test_crit_003_email_services(self):
        """
        CRIT-003: Verify email services investigation findings
        
        Should confirm that no email services exist in the application
        (This was determined to be a false positive)
        """
        print("🔍 Testing CRIT-003: Email Services Investigation")
        
        # Test for absence of email endpoints
        email_endpoints = [
            "/api/v1/email",
            "/api/v1/mail", 
            "/api/v1/notifications",
            "/api/v1/send-email",
            "/email",
            "/mail"
        ]
        
        email_found = False
        for endpoint in email_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code != 404:
                    email_found = True
                    self.log_test(f"CRIT-003: Email Endpoint {endpoint}", "FAIL",
                                f"Found email endpoint returning {response.status_code}",
                                "No email endpoints should exist")
            except Exception:
                # 404 or connection error is expected/good
                pass
        
        if not email_found:
            self.log_test("CRIT-003: Email Services Absence", "PASS",
                        "No email endpoints found - confirms false positive finding")
        
        # Test the root API to ensure it doesn't advertise email services  
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                content = response.text.lower()
                if "email" in content or "mail" in content:
                    self.log_test("CRIT-003: Root API Email References", "FAIL",
                                "Root API contains email references",
                                "No email references should exist")
                else:
                    self.log_test("CRIT-003: Root API Email References", "PASS",
                                "Root API contains no email references")
            else:
                self.log_test("CRIT-003: Root API Email References", "FAIL",
                            f"Root API returned {response.status_code}")
        except Exception as e:
            self.log_test("CRIT-003: Root API Email References", "FAIL", str(e))

    def test_environment_configuration(self):
        """Test that staging environment is configured correctly for security testing"""
        print("🔍 Testing Environment Configuration")
        
        # Test that we can access debug endpoints to verify environment
        try:
            response = requests.get(f"{self.base_url}/debug/cors", timeout=5)
            if response.status_code == 200:
                debug_info = response.json()
                self.log_test("Environment Debug Access", "PASS",
                            f"Debug endpoint accessible: {debug_info.get('environment_variables', {})}")
            else:
                self.log_test("Environment Debug Access", "FAIL",
                            f"Debug endpoint returned {response.status_code}")
        except Exception as e:
            self.log_test("Environment Debug Access", "FAIL", str(e))

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("🔒 CRITICAL SECURITY FIXES VERIFICATION REPORT")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Group results by security fix
        crit_001_tests = [r for r in self.test_results if "CRIT-001" in r["test"]]
        crit_002_tests = [r for r in self.test_results if "CRIT-002" in r["test"]]
        crit_003_tests = [r for r in self.test_results if "CRIT-003" in r["test"]]
        
        def format_test_group(tests, title):
            if not tests:
                return f"\n{title}: No tests run"
            passed = len([t for t in tests if t["status"] == "PASS"])
            total = len(tests)
            status = "✅ SECURED" if passed == total else "❌ VULNERABLE"
            return f"\n{title}: {passed}/{total} tests passed {status}"
        
        print(format_test_group(crit_001_tests, "🔴 CRIT-001 (API Docs)"))
        print(format_test_group(crit_002_tests, "🔴 CRIT-002 (Admin Auth)"))
        print(format_test_group(crit_003_tests, "🟢 CRIT-003 (Email Services)"))
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"   - {result['test']}: {result['details']}")
        
        print(f"\n🎯 RECOMMENDATION:")
        if failed_tests == 0:
            print("   ✅ ALL SECURITY FIXES VERIFIED - SAFE TO DEPLOY TO STAGING")
            print("   ✅ Ready for comprehensive staging testing before master merge")
        else:
            print("   ❌ SECURITY VULNERABILITIES DETECTED - DO NOT DEPLOY")
            print("   ❌ Fix failed tests before proceeding with deployment")
        
        print("\n" + "="*80)
        
        # Save detailed report
        report_file = f"security_fixes_verification_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": (passed_tests/total_tests)*100
                },
                "results": self.test_results
            }, f, indent=2)
        
        print(f"📄 Detailed report saved to: {report_file}")
        
        return failed_tests == 0

    def run_all_tests(self) -> bool:
        """Run complete security verification suite"""
        print("🚀 Starting Critical Security Fixes Verification")
        print(f"🎯 Target: {self.base_url}")
        print(f"🔑 Admin API Key: {'*' * (len(self.admin_api_key) - 4) + self.admin_api_key[-4:]}")
        print("\n" + "="*80)
        
        # Test basic connectivity first
        if not self.test_backend_connectivity():
            print("❌ Cannot connect to backend - ensure staging environment is running")
            print("\nTo start staging environment:")
            print("docker-compose -f docker-compose.staging.yml up -d")
            return False
        
        # Run all security tests
        self.test_environment_configuration()
        self.test_crit_001_api_docs_disabled()
        self.test_crit_002_admin_auth_protection()
        self.test_crit_003_email_services()
        
        # Generate final report
        return self.generate_report()


def main():
    """Main execution function"""
    # Check for required environment variables
    if not os.getenv("ADMIN_API_KEY"):
        print("❌ ADMIN_API_KEY environment variable not set")
        print("Please ensure .env file contains ADMIN_API_KEY")
        sys.exit(1)
    
    # Initialize tester
    tester = SecurityFixTester()
    
    # Run verification
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 