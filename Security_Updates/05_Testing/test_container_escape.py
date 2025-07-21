#!/usr/bin/env python3
"""
🚨 CRITICAL VULNERABILITY TEST: T-002 Worker Container Escape
CVSS: 9.1 (Critical)
Purpose: Test for container escape vulnerabilities in video processing worker
Environment: SECURITY TESTING ONLY - Isolated environment
"""

import subprocess
import json
import time
import os
from pathlib import Path

class ContainerEscapeTestor:
    def __init__(self):
        self.security_test_containers = [
            "meme-maker-worker-security-test",
            "meme-maker-backend-security-test"
        ]
        self.results = []
        
    def log_test(self, test_name, command, result, vulnerability_detected=False):
        """Log test results for analysis"""
        test_result = {
            "test": test_name,
            "command": command,
            "result": result,
            "vulnerability_detected": vulnerability_detected,
            "timestamp": time.time()
        }
        self.results.append(test_result)
        
        status_icon = "🚨" if vulnerability_detected else "✅"
        print(f"{status_icon} {test_name}: {command[:60]}...")
        
    def run_docker_command(self, container_name, command):
        """Execute command inside container and return result"""
        full_command = ["docker", "exec", container_name] + command.split()
        
        try:
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {"error": "Command timeout", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}
            
    def test_container_status(self):
        """Test 1: Verify containers are running and accessible"""
        print("\n🔍 TEST 1: Container Status and Accessibility")
        
        for container in self.security_test_containers:
            # Check if container is running
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={container}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True
            )
            
            is_running = container in result.stdout
            print(f"📦 Container {container}: {'✅ Running' if is_running else '❌ Not Found'}")
            
            if is_running:
                # Test basic command execution
                exec_result = self.run_docker_command(container, "whoami")
                self.log_test(
                    "Container Access",
                    f"docker exec {container} whoami",
                    exec_result,
                    False  # Basic access is expected
                )
                
    def test_container_isolation(self):
        """Test 2: Container isolation and privilege restrictions"""
        print("\n🚨 TEST 2: Container Isolation Testing")
        
        test_commands = [
            # Test filesystem isolation
            ("Host Root Access", "ls -la /"),
            ("Proc Filesystem", "cat /proc/1/cgroup"),
            ("Docker Socket Access", "ls -la /var/run/docker.sock"),
            
            # Test privilege escalation
            ("Sudo Access", "sudo -l"),
            ("Setuid Binaries", "find / -perm -u=s -type f 2>/dev/null | head -5"),
            
            # Test capability restrictions
            ("Network Admin", "ip addr"),
            ("Mount Operations", "mount"),
            
            # Test container escape techniques
            ("Host Process Tree", "ps aux | head -10"),
            ("Container Breakout", "cat /proc/mounts | grep docker"),
        ]
        
        for container in self.security_test_containers:
            print(f"\n📦 Testing {container}:")
            
            for test_name, command in test_commands:
                result = self.run_docker_command(container, command)
                
                # Analyze results for security issues
                vulnerability_detected = False
                if result.get("success"):
                    # Check for concerning outputs
                    output = result.get("stdout", "") + result.get("stderr", "")
                    
                    # Red flags that indicate potential escape vectors
                    red_flags = [
                        "/var/run/docker.sock",  # Docker socket access
                        "root",  # Running as root
                        "sudo",  # Sudo access
                        "/host",  # Host filesystem access
                        "privileged"  # Privileged mode
                    ]
                    
                    for flag in red_flags:
                        if flag.lower() in output.lower():
                            vulnerability_detected = True
                            break
                            
                self.log_test(
                    f"{test_name} ({container})",
                    command,
                    result,
                    vulnerability_detected
                )
                
    def test_resource_limits(self):
        """Test 3: Container resource limit enforcement"""
        print("\n🔍 TEST 3: Resource Limit Enforcement")
        
        resource_tests = [
            # Memory limits
            ("Memory Limit", "cat /sys/fs/cgroup/memory/memory.limit_in_bytes"),
            ("Memory Usage", "cat /proc/meminfo | grep MemTotal"),
            
            # CPU limits  
            ("CPU Quota", "cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us"),
            ("CPU Shares", "cat /sys/fs/cgroup/cpu/cpu.shares"),
            
            # Process limits
            ("Process Limit", "cat /sys/fs/cgroup/pids/pids.max"),
            ("Current Processes", "ps aux | wc -l"),
        ]
        
        for container in self.security_test_containers:
            print(f"\n📦 Testing {container} resource limits:")
            
            for test_name, command in resource_tests:
                result = self.run_docker_command(container, command)
                
                # Check if limits are properly enforced
                unlimited_detected = False
                if result.get("success"):
                    output = result.get("stdout", "")
                    
                    # Check for unlimited or very high limits (potential issue)
                    if any(indicator in output for indicator in ["-1", "max", "unlimited", "9223372036854775807"]):
                        unlimited_detected = True
                        
                self.log_test(
                    f"{test_name} ({container})",
                    command,
                    result,
                    unlimited_detected
                )
                
    def test_security_profiles(self):
        """Test 4: Security profile enforcement (AppArmor, SELinux, seccomp)"""
        print("\n🔒 TEST 4: Security Profile Enforcement")
        
        security_tests = [
            # AppArmor
            ("AppArmor Status", "cat /proc/self/attr/current"),
            
            # Seccomp
            ("Seccomp Mode", "cat /proc/self/status | grep Seccomp"),
            
            # Capabilities
            ("Process Capabilities", "cat /proc/self/status | grep Cap"),
            
            # Namespace isolation
            ("PID Namespace", "readlink /proc/self/ns/pid"),
            ("Network Namespace", "readlink /proc/self/ns/net"),
            ("Mount Namespace", "readlink /proc/self/ns/mnt"),
        ]
        
        for container in self.security_test_containers:
            print(f"\n🔒 Testing {container} security profiles:")
            
            for test_name, command in security_tests:
                result = self.run_docker_command(container, command)
                
                # Analyze security profile effectiveness
                weak_security = False
                if result.get("success"):
                    output = result.get("stdout", "")
                    
                    # Check for weak security configurations
                    if any(weak_indicator in output.lower() for weak_indicator in [
                        "unconfined", "disabled", "0000000000000000"
                    ]):
                        weak_security = True
                        
                self.log_test(
                    f"{test_name} ({container})",
                    command,
                    result,
                    weak_security
                )
                
    def test_host_system_access(self):
        """Test 5: Attempt to access host system from container"""
        print("\n🚨 TEST 5: Host System Access Attempts")
        
        host_access_tests = [
            # Host filesystem access attempts
            ("Host Root FS", "ls -la /host/"),
            ("Host Proc FS", "ls -la /host/proc/"),
            ("Host Etc Access", "cat /host/etc/hostname"),
            
            # Host network access
            ("Host Network", "netstat -tuln"),
            ("Host Services", "ss -tuln"),
            
            # Host device access
            ("Device Files", "ls -la /dev/"),
            ("Block Devices", "lsblk"),
        ]
        
        for container in self.security_test_containers:
            print(f"\n🚨 Testing {container} host access:")
            
            for test_name, command in host_access_tests:
                result = self.run_docker_command(container, command)
                
                # Host access is a critical vulnerability
                host_access_detected = result.get("success", False)
                
                self.log_test(
                    f"{test_name} ({container})",
                    command,
                    result,
                    host_access_detected
                )
                
    def generate_report(self):
        """Generate comprehensive container escape test report"""
        print("\n" + "="*80)
        print("🚨 CRITICAL VULNERABILITY TEST REPORT: T-002 Container Escape")
        print("="*80)
        
        total_tests = len(self.results)
        vulnerabilities_detected = sum(1 for r in self.results if r["vulnerability_detected"])
        
        print(f"📊 SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Vulnerabilities Detected: {vulnerabilities_detected}")
        print(f"   Security Risk Level: {'🚨 CRITICAL' if vulnerabilities_detected > 0 else '✅ LOW'}")
        
        if vulnerabilities_detected > 0:
            print(f"\n⚠️ CRITICAL FINDINGS:")
            print(f"   {vulnerabilities_detected} out of {total_tests} tests detected container escape vectors")
            print(f"   This confirms T-002 (CVSS 9.1) vulnerability exists")
            print(f"   IMMEDIATE ACTION REQUIRED: Enhanced container security")
            
            print(f"\n🚨 VULNERABLE TESTS:")
            for result in self.results:
                if result["vulnerability_detected"]:
                    print(f"   - {result['test']}: {result['command']}")
                    
        print(f"\n📝 RECOMMENDATIONS:")
        print(f"   1. Implement gVisor/rootless containers")
        print(f"   2. Drop all capabilities and add only required ones")
        print(f"   3. Enable seccomp profiles")
        print(f"   4. Remove host filesystem mounts")
        print(f"   5. Implement resource limits")
        
        # Save detailed results
        with open("logs-security-test/t002_container_escape_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
            
        print(f"\n💾 Detailed results saved to: logs-security-test/t002_container_escape_results.json")
        
    def run_all_tests(self):
        """Execute complete container escape test suite"""
        print("🚨 STARTING CRITICAL VULNERABILITY TEST: T-002 Container Escape")
        print("Environment: Isolated Security Testing")
        print("="*80)
        
        # Execute all test categories
        self.test_container_status()
        self.test_container_isolation()
        self.test_resource_limits()
        self.test_security_profiles()
        self.test_host_system_access()
        
        # Generate comprehensive report
        self.generate_report()
        
        return True

if __name__ == "__main__":
    print("🚨 T-002 Container Escape Vulnerability Tester")
    print("SECURITY TESTING ENVIRONMENT ONLY")
    print("Do NOT run against production systems")
    print()
    
    tester = ContainerEscapeTestor()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ T-002 Container Escape Testing Complete")
        print("📋 Next: Review results and proceed to T-003 Queue DoS Testing")
    else:
        print("\n❌ T-002 Testing Failed - Environment Issues") 