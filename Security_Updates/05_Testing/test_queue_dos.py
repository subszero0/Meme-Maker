#!/usr/bin/env python3
"""
🚨 CRITICAL VULNERABILITY TEST: T-003 Queue Draining DoS
CVSS: 8.6 (High)
Purpose: Test for queue exhaustion and DoS vulnerabilities
Environment: SECURITY TESTING ONLY - Isolated environment
"""

import requests
import json
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

SECURITY_TEST_BASE_URL = "http://localhost:8001"
TIMEOUT = 30

class QueueDoSTestor:
    def __init__(self):
        self.base_url = SECURITY_TEST_BASE_URL
        self.session = requests.Session()
        self.results = []
        self.job_responses = []
        
    def log_test(self, test_name, description, result, vulnerability_detected=False):
        """Log test results for analysis"""
        test_result = {
            "test": test_name,
            "description": description,
            "result": result,
            "vulnerability_detected": vulnerability_detected,
            "timestamp": time.time()
        }
        self.results.append(test_result)
        
        status_icon = "🚨" if vulnerability_detected else "✅"
        print(f"{status_icon} {test_name}: {description}")
        
    def submit_job(self, url, in_ts=0, out_ts=10, session_id=None):
        """Submit a single job to the queue"""
        data = {
            "url": url,
            "in_ts": in_ts,
            "out_ts": out_ts
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/jobs",
                json=data,
                timeout=TIMEOUT
            )
            
            result = {
                "status_code": response.status_code,
                "success": response.status_code == 201,
                "response_time": response.elapsed.total_seconds(),
                "session_id": session_id,
                "timestamp": time.time()
            }
            
            if response.status_code == 201:
                result["job_id"] = response.json().get("id")
                
            return result
            
        except Exception as e:
            return {
                "status_code": None,
                "success": False,
                "error": str(e),
                "session_id": session_id,
                "timestamp": time.time()
            }
            
    def test_basic_rate_limiting(self):
        """Test 1: Basic rate limiting effectiveness"""
        print("\n🔍 TEST 1: Basic Rate Limiting")
        
        # Submit jobs rapidly to test rate limiting
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        successful_jobs = 0
        rate_limited_jobs = 0
        
        print("📤 Submitting 10 rapid jobs...")
        for i in range(10):
            result = self.submit_job(test_url)
            self.job_responses.append(result)
            
            if result["success"]:
                successful_jobs += 1
            elif result["status_code"] == 429:  # Too Many Requests
                rate_limited_jobs += 1
                
            # Very short delay between requests
            time.sleep(0.1)
            
        rate_limiting_effective = rate_limited_jobs > 0 or successful_jobs < 10
        
        self.log_test(
            "Basic Rate Limiting",
            f"Submitted 10 jobs: {successful_jobs} successful, {rate_limited_jobs} rate-limited",
            {
                "successful_jobs": successful_jobs,
                "rate_limited_jobs": rate_limited_jobs,
                "total_jobs": 10
            },
            not rate_limiting_effective  # Vulnerability if no rate limiting
        )
        
    def test_concurrent_job_submission(self):
        """Test 2: Concurrent job submission stress test"""
        print("\n🚨 TEST 2: Concurrent Job Submission")
        
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        concurrent_jobs = 20
        successful_submissions = 0
        failed_submissions = 0
        response_times = []
        
        def submit_concurrent_job(session_id):
            return self.submit_job(test_url, session_id=session_id)
            
        print(f"📤 Submitting {concurrent_jobs} concurrent jobs...")
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_jobs) as executor:
            future_to_session = {
                executor.submit(submit_concurrent_job, i): i 
                for i in range(concurrent_jobs)
            }
            
            for future in as_completed(future_to_session):
                session_id = future_to_session[future]
                try:
                    result = future.result()
                    self.job_responses.append(result)
                    
                    if result["success"]:
                        successful_submissions += 1
                        if "response_time" in result:
                            response_times.append(result["response_time"])
                    else:
                        failed_submissions += 1
                        
                except Exception as e:
                    failed_submissions += 1
                    print(f"⚠️ Job {session_id} exception: {e}")
                    
        total_time = time.time() - start_time
        avg_response_time = statistics.mean(response_times) if response_times else 0
        
        # High success rate with concurrent requests indicates potential DoS vulnerability
        vulnerability_detected = successful_submissions > (concurrent_jobs * 0.8)
        
        self.log_test(
            "Concurrent Submission",
            f"{successful_submissions}/{concurrent_jobs} jobs succeeded, avg response: {avg_response_time:.2f}s",
            {
                "successful_submissions": successful_submissions,
                "failed_submissions": failed_submissions,
                "total_time": total_time,
                "avg_response_time": avg_response_time
            },
            vulnerability_detected
        )
        
    def test_resource_intensive_jobs(self):
        """Test 3: Resource-intensive job submission"""
        print("\n🚨 TEST 3: Resource-Intensive Jobs")
        
        # Test with longer videos and longer clips
        resource_intensive_jobs = [
            {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", 
                "in_ts": 0, 
                "out_ts": 180,  # 3 minutes (max allowed)
                "description": "Max duration clip"
            },
            {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", 
                "in_ts": 0, 
                "out_ts": 60,
                "description": "1 minute clip"
            },
            {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", 
                "in_ts": 0, 
                "out_ts": 120,
                "description": "2 minute clip"
            }
        ]
        
        successful_intensive_jobs = 0
        
        for job_config in resource_intensive_jobs:
            print(f"📤 Submitting {job_config['description']}...")
            result = self.submit_job(
                job_config["url"], 
                job_config["in_ts"], 
                job_config["out_ts"]
            )
            self.job_responses.append(result)
            
            if result["success"]:
                successful_intensive_jobs += 1
                
            time.sleep(1)  # Brief delay between intensive jobs
            
        # All intensive jobs being accepted could indicate resource exhaustion vulnerability
        vulnerability_detected = successful_intensive_jobs == len(resource_intensive_jobs)
        
        self.log_test(
            "Resource Intensive Jobs",
            f"{successful_intensive_jobs}/{len(resource_intensive_jobs)} intensive jobs accepted",
            {
                "successful_intensive_jobs": successful_intensive_jobs,
                "total_intensive_jobs": len(resource_intensive_jobs)
            },
            vulnerability_detected
        )
        
    def test_queue_capacity_limits(self):
        """Test 4: Queue capacity and overflow handling"""
        print("\n🔍 TEST 4: Queue Capacity Limits")
        
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        queue_flood_jobs = 30  # Attempt to exceed typical queue limits
        successful_queued = 0
        queue_full_responses = 0
        
        print(f"📤 Attempting to queue {queue_flood_jobs} jobs...")
        
        for i in range(queue_flood_jobs):
            result = self.submit_job(test_url)
            self.job_responses.append(result)
            
            if result["success"]:
                successful_queued += 1
            elif result["status_code"] == 503:  # Service Unavailable (queue full)
                queue_full_responses += 1
                
            # Small delay to avoid overwhelming the system too quickly
            time.sleep(0.2)
            
            # Stop if we get clear queue full responses
            if queue_full_responses >= 5:
                print(f"ℹ️ Stopping after {i+1} jobs due to queue full responses")
                break
                
        # Vulnerability if all jobs are accepted without queue management
        vulnerability_detected = successful_queued > 25 and queue_full_responses == 0
        
        self.log_test(
            "Queue Capacity",
            f"{successful_queued} jobs queued, {queue_full_responses} queue-full responses",
            {
                "successful_queued": successful_queued,
                "queue_full_responses": queue_full_responses,
                "attempted_jobs": min(queue_flood_jobs, successful_queued + queue_full_responses + 5)
            },
            vulnerability_detected
        )
        
    def test_malicious_url_resource_exhaustion(self):
        """Test 5: Malicious URL patterns for resource exhaustion"""
        print("\n🚨 TEST 5: Malicious URL Resource Exhaustion")
        
        malicious_urls = [
            # Very long URLs
            "https://example.com/video.mp4?" + "a" * 1000,
            
            # URLs with many parameters
            "https://example.com/video.mp4?" + "&".join([f"param{i}=value{i}" for i in range(100)]),
            
            # URLs designed to cause processing delays
            "https://httpbin.org/delay/10",  # Simulates slow response
            
            # Non-existent domains (DNS timeout)
            "https://this-domain-should-not-exist-12345.com/video.mp4",
        ]
        
        malicious_jobs_accepted = 0
        processing_times = []
        
        for url in malicious_urls:
            print(f"📤 Testing malicious URL: {url[:60]}...")
            start_time = time.time()
            
            result = self.submit_job(url, 0, 10)
            processing_time = time.time() - start_time
            processing_times.append(processing_time)
            
            self.job_responses.append(result)
            
            if result["success"]:
                malicious_jobs_accepted += 1
                
            time.sleep(1)
            
        avg_processing_time = statistics.mean(processing_times)
        
        # Accepting malicious URLs indicates potential DoS vulnerability
        vulnerability_detected = malicious_jobs_accepted > 0 or avg_processing_time > 5
        
        self.log_test(
            "Malicious URL Processing",
            f"{malicious_jobs_accepted}/{len(malicious_urls)} malicious URLs accepted, avg time: {avg_processing_time:.2f}s",
            {
                "malicious_jobs_accepted": malicious_jobs_accepted,
                "total_malicious_urls": len(malicious_urls),
                "avg_processing_time": avg_processing_time
            },
            vulnerability_detected
        )
        
    def check_service_availability_during_tests(self):
        """Test 6: Service availability during stress testing"""
        print("\n🔍 TEST 6: Service Availability During Stress")
        
        # Test if basic health endpoint is still responsive
        health_checks = []
        
        for i in range(5):
            try:
                start_time = time.time()
                response = self.session.get(f"{self.base_url}/health", timeout=10)
                response_time = time.time() - start_time
                
                health_checks.append({
                    "success": response.status_code == 200,
                    "response_time": response_time,
                    "status_code": response.status_code
                })
                
            except Exception as e:
                health_checks.append({
                    "success": False,
                    "error": str(e),
                    "response_time": 10  # Timeout
                })
                
            time.sleep(2)
            
        successful_health_checks = sum(1 for check in health_checks if check["success"])
        avg_health_response_time = statistics.mean([
            check["response_time"] for check in health_checks if "response_time" in check
        ])
        
        # Service degradation indicates potential DoS impact
        service_degraded = successful_health_checks < 4 or avg_health_response_time > 2
        
        self.log_test(
            "Service Availability",
            f"{successful_health_checks}/5 health checks passed, avg response: {avg_health_response_time:.2f}s",
            {
                "successful_health_checks": successful_health_checks,
                "avg_health_response_time": avg_health_response_time
            },
            service_degraded
        )
        
    def generate_report(self):
        """Generate comprehensive queue DoS test report"""
        print("\n" + "="*80)
        print("🚨 CRITICAL VULNERABILITY TEST REPORT: T-003 Queue DoS")
        print("="*80)
        
        total_tests = len(self.results)
        vulnerabilities_detected = sum(1 for r in self.results if r["vulnerability_detected"])
        total_jobs_submitted = len(self.job_responses)
        successful_jobs = sum(1 for job in self.job_responses if job["success"])
        
        print(f"📊 SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Vulnerabilities Detected: {vulnerabilities_detected}")
        print(f"   Total Jobs Submitted: {total_jobs_submitted}")
        print(f"   Successful Job Submissions: {successful_jobs}")
        print(f"   Security Risk Level: {'🚨 CRITICAL' if vulnerabilities_detected > 0 else '✅ LOW'}")
        
        if vulnerabilities_detected > 0:
            print(f"\n⚠️ CRITICAL FINDINGS:")
            print(f"   {vulnerabilities_detected} out of {total_tests} tests detected DoS vulnerabilities")
            print(f"   This confirms T-003 (CVSS 8.6) vulnerability exists")
            print(f"   IMMEDIATE ACTION REQUIRED: Enhanced rate limiting and queue management")
            
            print(f"\n🚨 VULNERABLE TESTS:")
            for result in self.results:
                if result["vulnerability_detected"]:
                    print(f"   - {result['test']}: {result['description']}")
                    
        print(f"\n📝 RECOMMENDATIONS:")
        print(f"   1. Implement IP-based rate limiting (5 jobs/IP/hour)")
        print(f"   2. Add queue depth monitoring and alerts") 
        print(f"   3. Implement circuit breaker pattern")
        print(f"   4. Add resource-based job prioritization")
        print(f"   5. Deploy DDoS protection service")
        
        # Save detailed results
        with open("logs-security-test/t003_queue_dos_results.json", "w") as f:
            json.dump({
                "test_results": self.results,
                "job_responses": self.job_responses
            }, f, indent=2)
            
        print(f"\n💾 Detailed results saved to: logs-security-test/t003_queue_dos_results.json")
        
    def run_all_tests(self):
        """Execute complete queue DoS test suite"""
        print("🚨 STARTING CRITICAL VULNERABILITY TEST: T-003 Queue DoS")
        print("Environment: Isolated Security Testing (localhost:8001)")
        print("="*80)
        
        # Verify service is accessible
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code != 200:
                print("❌ Cannot proceed - security test environment not accessible")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to security test environment: {e}")
            return False
            
        print("✅ Security test environment is accessible")
        
        # Execute all test categories
        self.test_basic_rate_limiting()
        self.test_concurrent_job_submission()
        self.test_resource_intensive_jobs()
        self.test_queue_capacity_limits()
        self.test_malicious_url_resource_exhaustion()
        self.check_service_availability_during_tests()
        
        # Generate comprehensive report
        self.generate_report()
        
        return True

if __name__ == "__main__":
    print("🚨 T-003 Queue DoS Vulnerability Tester")
    print("SECURITY TESTING ENVIRONMENT ONLY")
    print("Do NOT run against production systems")
    print()
    
    # Confirm this is security testing
    if "8001" not in SECURITY_TEST_BASE_URL:
        print("❌ ERROR: Not configured for security testing environment")
        exit(1)
        
    tester = QueueDoSTestor()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ T-003 Queue DoS Testing Complete")
        print("📋 Next: All 3 CRITICAL vulnerability tests completed - proceed to Phase 1.1")
    else:
        print("\n❌ T-003 Testing Failed - Environment Issues") 