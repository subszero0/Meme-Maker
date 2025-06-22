#!/usr/bin/env python3
"""
Diagnostic Script for API Connection Issue
Checks each stage systematically following best practices
"""

import subprocess
import requests
import json
import time
import os
from datetime import datetime

class ConnectionDiagnostics:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.results = {}
        
    def log(self, message, status="INFO"):
        print(f"[{status}] {message}")
        
    def test_docker_status(self):
        """Stage 1: Check Docker Desktop status"""
        self.log("🐳 Stage 1: Testing Docker Desktop Status", "INFO")
        
        try:
            result = subprocess.run(['docker', 'version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.log("✅ Docker Desktop is running", "PASS")
                self.results['docker_status'] = True
                return True
            else:
                self.log("❌ Docker Desktop not running or not accessible", "FAIL")
                self.log(f"   Error: {result.stderr}", "FAIL")
                self.results['docker_status'] = False
                return False
        except subprocess.TimeoutExpired:
            self.log("❌ Docker command timed out", "FAIL")
            self.results['docker_status'] = False
            return False
        except Exception as e:
            self.log(f"❌ Docker check failed: {e}", "FAIL")
            self.results['docker_status'] = False
            return False
    
    def test_containers_status(self):
        """Stage 2: Check container status"""
        self.log("📦 Stage 2: Testing Container Status", "INFO")
        
        if not self.results.get('docker_status'):
            self.log("⚠️  Skipping container check - Docker not running", "SKIP")
            self.results['containers_status'] = False
            return False
            
        try:
            # Check development containers
            result = subprocess.run(['docker-compose', '-f', 'docker-compose.dev.yaml', 'ps'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                output = result.stdout
                containers = ['meme-maker-backend-dev', 'meme-maker-frontend-dev', 'meme-maker-worker-dev', 'meme-maker-redis-dev']
                
                running_containers = []
                for container in containers:
                    if container in output and 'Up' in output:
                        running_containers.append(container)
                        self.log(f"✅ {container}: Running", "PASS")
                    else:
                        self.log(f"❌ {container}: Not running", "FAIL")
                
                if len(running_containers) == len(containers):
                    self.log("✅ All development containers running", "PASS")
                    self.results['containers_status'] = True
                    return True
                else:
                    self.log(f"❌ Only {len(running_containers)}/{len(containers)} containers running", "FAIL")
                    self.results['containers_status'] = False
                    return False
            else:
                self.log("❌ Failed to get container status", "FAIL")
                self.log(f"   Error: {result.stderr}", "FAIL")
                self.results['containers_status'] = False
                return False
                
        except Exception as e:
            self.log(f"❌ Container status check failed: {e}", "FAIL")
            self.results['containers_status'] = False
            return False
    
    def test_backend_connectivity(self):
        """Stage 3: Test backend API connectivity"""
        self.log("🔌 Stage 3: Testing Backend API Connectivity", "INFO")
        
        api_urls = [
            ("http://localhost:8000/health", "Health Check"),
            ("http://localhost:8000/api/v1/metadata", "Metadata Endpoint"),
        ]
        
        backend_working = True
        
        for url, description in api_urls:
            try:
                if "metadata" in url:
                    # Test metadata endpoint with POST
                    response = requests.post(url, 
                                           json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}, 
                                           timeout=10)
                else:
                    # Test health endpoint with GET
                    response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    self.log(f"✅ {description}: HTTP {response.status_code}", "PASS")
                else:
                    self.log(f"❌ {description}: HTTP {response.status_code}", "FAIL")
                    backend_working = False
                    
            except requests.exceptions.ConnectionError:
                self.log(f"❌ {description}: Connection refused", "FAIL")
                backend_working = False
            except requests.exceptions.Timeout:
                self.log(f"❌ {description}: Timeout", "FAIL")
                backend_working = False
            except Exception as e:
                self.log(f"❌ {description}: {e}", "FAIL")
                backend_working = False
        
        self.results['backend_connectivity'] = backend_working
        return backend_working
    
    def test_frontend_config(self):
        """Stage 4: Check frontend configuration"""
        self.log("⚙️ Stage 4: Testing Frontend Configuration", "INFO")
        
        try:
            # Check if frontend is running on port 3000
            response = requests.get("http://localhost:3000", timeout=5)
            if response.status_code == 200:
                self.log("✅ Frontend accessible at http://localhost:3000", "PASS")
                
                # Check if it's making correct API calls
                content = response.text
                if "localhost:8000" in content:
                    self.log("⚠️  Frontend config references localhost:8000", "WARN")
                    self.log("   This is expected in development mode", "INFO")
                else:
                    self.log("✅ Frontend using relative URLs", "PASS")
                    
                self.results['frontend_config'] = True
                return True
            else:
                self.log(f"❌ Frontend returned HTTP {response.status_code}", "FAIL")
                self.results['frontend_config'] = False
                return False
                
        except requests.exceptions.ConnectionError:
            self.log("❌ Frontend not accessible (connection refused)", "FAIL")
            self.results['frontend_config'] = False
            return False
        except Exception as e:
            self.log(f"❌ Frontend check failed: {e}", "FAIL")
            self.results['frontend_config'] = False
            return False
    
    def provide_solution(self):
        """Stage 5: Provide targeted solution based on findings"""
        self.log("🎯 Stage 5: Solution Analysis", "INFO")
        
        if not self.results.get('docker_status'):
            self.log("🔧 SOLUTION: Start Docker Desktop", "ACTION")
            self.log("   1. Open Docker Desktop application", "ACTION")
            self.log("   2. Wait for Docker to start completely", "ACTION")
            self.log("   3. Run: docker version (to verify)", "ACTION")
            
        elif not self.results.get('containers_status'):
            self.log("🔧 SOLUTION: Start development containers", "ACTION")
            self.log("   1. Run: docker-compose -f docker-compose.dev.yaml up -d", "ACTION")
            self.log("   2. Wait for all containers to be healthy", "ACTION")
            self.log("   3. Check: docker-compose -f docker-compose.dev.yaml ps", "ACTION")
            
        elif not self.results.get('backend_connectivity'):
            self.log("🔧 SOLUTION: Backend container issues", "ACTION")
            self.log("   1. Check backend logs: docker-compose -f docker-compose.dev.yaml logs backend", "ACTION")
            self.log("   2. Restart backend: docker-compose -f docker-compose.dev.yaml restart backend", "ACTION")
            
        elif not self.results.get('frontend_config'):
            self.log("🔧 SOLUTION: Frontend container issues", "ACTION")
            self.log("   1. Check frontend logs: docker-compose -f docker-compose.dev.yaml logs frontend", "ACTION")
            self.log("   2. Restart frontend: docker-compose -f docker-compose.dev.yaml restart frontend", "ACTION")
            
        else:
            self.log("✅ All systems operational - investigate specific errors", "ACTION")
    
    def run_diagnosis(self):
        """Run complete diagnosis"""
        self.log(f"🔍 CONNECTION DIAGNOSTICS STARTED - {self.timestamp}", "START")
        self.log("=" * 60, "INFO")
        
        # Run all diagnostic stages
        self.test_docker_status()
        self.test_containers_status()
        self.test_backend_connectivity()
        self.test_frontend_config()
        
        # Summary
        self.log("=" * 60, "INFO")
        self.log("📊 DIAGNOSTIC SUMMARY", "SUMMARY")
        
        passed = sum(1 for result in self.results.values() if result is True)
        total = len(self.results)
        
        for test_name, result in self.results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"   {status} {test_name.replace('_', ' ').title()}", "SUMMARY")
        
        self.log(f"📈 Results: {passed}/{total} stages passed", "SUMMARY")
        
        # Provide solution
        self.provide_solution()
        
        return self.results

if __name__ == "__main__":
    diagnostics = ConnectionDiagnostics()
    results = diagnostics.run_diagnosis() 