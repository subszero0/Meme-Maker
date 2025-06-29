#!/usr/bin/env python3
"""
Production 502 Error Diagnostics
================================
This script helps diagnose why the production backend is returning 502 Bad Gateway.

Based on ground truth:
- Frontend: ✅ Working (200 OK) 
- API Backend: ❌ Failing (502 Bad Gateway from nginx)
- Issue: nginx cannot connect to backend container on port 8000

Following Best Practices:
- #0: Environment context confirmed (production memeit.pro)
- #1: Ground truth established via direct testing
- #18: Deployment pipeline issue, not code issue
"""

import requests
import subprocess
import json
from datetime import datetime


class Production502Diagnostics:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def log(self, message, status="INFO"):
        print(f"[{status}] {message}")
        
    def test_production_endpoints(self):
        """Test all production endpoints to confirm the 502 scope"""
        self.log("🌍 Testing Production Endpoints", "INFO")
        
        endpoints = [
            ("https://memeit.pro", "Frontend"),
            ("https://memeit.pro/api/v1/health", "Backend Health"),
            ("https://memeit.pro/api/v1/metadata", "Backend API"),
            ("http://memeit.pro", "HTTP Frontend"),
            ("http://memeit.pro/api/v1/health", "HTTP Backend Health"),
        ]
        
        results = {}
        for url, name in endpoints:
            try:
                if 'metadata' in url:
                    response = requests.post(url, 
                                           json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}, 
                                           timeout=10)
                else:
                    response = requests.get(url, timeout=10)
                
                status = f"{response.status_code} {response.reason}"
                self.log(f"  {name}: {status}", "PASS" if response.status_code == 200 else "FAIL")
                results[name] = {"status": response.status_code, "reason": response.reason}
                
            except Exception as e:
                error_msg = str(e)
                self.log(f"  {name}: ERROR - {error_msg}", "FAIL")
                results[name] = {"error": error_msg}
        
        return results
    
    def check_deployment_hypothesis(self):
        """Check common deployment issues that cause 502 errors"""
        self.log("🔍 Checking Deployment Hypotheses", "INFO")
        
        hypotheses = [
            "Backend container not running",
            "Backend container running but unhealthy",
            "Backend container running on wrong port",
            "nginx reverse proxy misconfigured",
            "Docker networking issues",
            "Backend startup failure (check logs)",
            "Environment variable misconfiguration",
            "Recent deployment failed partially"
        ]
        
        self.log("  Possible causes of 502 Bad Gateway:", "INFO")
        for i, hypothesis in enumerate(hypotheses, 1):
            self.log(f"    {i}. {hypothesis}", "INFO")
    
    def generate_ssh_diagnostic_commands(self):
        """Generate commands to run on the production server via SSH"""
        self.log("🔧 SSH Diagnostic Commands for Production Server", "INFO")
        self.log("  Run these commands on the production server:", "INFO")
        
        commands = [
            "# Check if containers are running",
            "docker ps",
            "",
            "# Check container health status",
            "docker-compose ps",
            "",
            "# Check backend container logs",
            "docker-compose logs backend --tail=50",
            "",
            "# Test backend directly on host",
            "curl -I http://localhost:8000/health",
            "",
            "# Test nginx access to backend",
            "curl -I http://127.0.0.1:8000/health",
            "",
            "# Check nginx error logs",
            "sudo tail -50 /var/log/nginx/error.log",
            "",
            "# Check what's listening on port 8000",
            "sudo netstat -tlnp | grep :8000",
            "",
            "# Check recent deployment logs",
            "sudo journalctl -u docker -n 50",
        ]
        
        for cmd in commands:
            if cmd.startswith("#"):
                self.log(f"  {cmd}", "INFO")
            elif cmd == "":
                print()
            else:
                self.log(f"    {cmd}", "CMD")
    
    def generate_fix_hypotheses(self):
        """Generate potential fixes based on common 502 causes"""
        self.log("🛠️ Potential Fix Strategies", "INFO")
        
        fixes = [
            {
                "hypothesis": "Backend container crashed/stopped",
                "test": "docker ps | grep backend",
                "fix": "docker-compose up -d backend"
            },
            {
                "hypothesis": "Backend container unhealthy",
                "test": "docker-compose ps",
                "fix": "docker-compose restart backend"
            },
            {
                "hypothesis": "Backend startup failure",
                "test": "docker-compose logs backend",
                "fix": "Fix startup error in logs, then docker-compose up -d backend"
            },
            {
                "hypothesis": "Port 8000 not accessible",
                "test": "curl http://localhost:8000/health",
                "fix": "Check docker-compose.yaml port mapping"
            },
            {
                "hypothesis": "nginx misconfiguration",
                "test": "sudo nginx -t",
                "fix": "Fix nginx config and sudo systemctl reload nginx"
            },
            {
                "hypothesis": "Recent deployment failed",
                "test": "git log -1 --oneline",
                "fix": "Re-run deployment or rollback to last working commit"
            }
        ]
        
        for i, fix in enumerate(fixes, 1):
            self.log(f"  {i}. {fix['hypothesis']}", "INFO")
            self.log(f"     Test: {fix['test']}", "CMD")
            self.log(f"     Fix:  {fix['fix']}", "FIX")
            print()
    
    def test_local_environment_status(self):
        """Check if local environment is running (should be irrelevant to production)"""
        self.log("🏠 Local Environment Status (for context only)", "INFO")
        
        try:
            result = subprocess.run(['docker', 'ps'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                running_containers = [line for line in result.stdout.split('\n') 
                                    if 'meme-maker' in line]
                if running_containers:
                    self.log("  Local containers running (irrelevant to production 502):", "INFO")
                    for container in running_containers:
                        self.log(f"    {container.strip()}", "INFO")
                else:
                    self.log("  No local meme-maker containers running", "INFO")
            else:
                self.log("  Docker not available locally", "INFO")
                
        except Exception as e:
            self.log(f"  Cannot check local Docker: {e}", "INFO")
    
    def run_diagnosis(self):
        """Run complete 502 error diagnosis"""
        self.log("🚨 PRODUCTION 502 ERROR DIAGNOSIS", "START")
        self.log("=" * 60, "INFO")
        self.log(f"Timestamp: {self.timestamp}", "INFO")
        self.log("Environment: Production (memeit.pro)", "INFO")
        print()
        
        # Test current production status
        results = self.test_production_endpoints()
        print()
        
        # Check deployment hypotheses
        self.check_deployment_hypothesis()
        print()
        
        # Generate SSH diagnostic commands
        self.generate_ssh_diagnostic_commands()
        print()
        
        # Generate fix strategies
        self.generate_fix_hypotheses()
        print()
        
        # Check local environment (for context)
        self.test_local_environment_status()
        print()
        
        self.log("=" * 60, "INFO")
        self.log("🎯 SUMMARY", "INFO")
        self.log("The 502 Bad Gateway indicates nginx cannot reach the backend container.", "INFO")
        self.log("This is a deployment/infrastructure issue, not a code issue.", "INFO")
        self.log("Next step: SSH to production server and run diagnostic commands above.", "INFO")
        
        return results


if __name__ == "__main__":
    diagnostics = Production502Diagnostics()
    diagnostics.run_diagnosis() 