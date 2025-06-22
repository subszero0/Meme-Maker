#!/usr/bin/env python3
"""
Development Environment Startup Script
Automatically starts Docker Desktop and development containers
"""

import subprocess
import time
import requests
import sys
from datetime import datetime

class DevelopmentStarter:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def log(self, message, status="INFO"):
        print(f"[{status}] {message}")
        
    def check_docker_desktop(self):
        """Check if Docker Desktop is running"""
        self.log("🐳 Checking Docker Desktop status...", "INFO")
        
        try:
            result = subprocess.run(['docker', 'version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.log("✅ Docker Desktop is running", "PASS")
                return True
            else:
                self.log("❌ Docker Desktop not running", "FAIL")
                return False
        except Exception:
            self.log("❌ Docker Desktop not accessible", "FAIL")
            return False
    
    def wait_for_docker(self, max_wait_time=120):
        """Wait for Docker Desktop to start"""
        self.log("⏳ Waiting for Docker Desktop to start...", "INFO")
        self.log("   Please start Docker Desktop if it's not already starting", "INFO")
        
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            if self.check_docker_desktop():
                return True
            
            elapsed = int(time.time() - start_time)
            remaining = max_wait_time - elapsed
            self.log(f"   Waiting... ({remaining}s remaining)", "WAIT")
            time.sleep(5)
        
        self.log("❌ Timeout waiting for Docker Desktop", "FAIL")
        return False
    
    def start_containers(self):
        """Start development containers"""
        self.log("📦 Starting development containers...", "INFO")
        
        try:
            # Start containers in detached mode
            result = subprocess.run([
                'docker-compose', '-f', 'docker-compose.dev.yaml', 'up', '-d'
            ], capture_output=True, text=True, timeout=180)
            
            if result.returncode == 0:
                self.log("✅ Containers started successfully", "PASS")
                return True
            else:
                self.log("❌ Failed to start containers", "FAIL")
                self.log(f"   Error: {result.stderr}", "FAIL")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("❌ Container startup timed out", "FAIL")
            return False
        except Exception as e:
            self.log(f"❌ Container startup failed: {e}", "FAIL")
            return False
    
    def wait_for_services(self):
        """Wait for services to be healthy"""
        self.log("🔌 Waiting for services to be ready...", "INFO")
        
        services = [
            ("http://localhost:8000/health", "Backend API"),
            ("http://localhost:3000", "Frontend"),
        ]
        
        max_wait = 60
        for url, service_name in services:
            self.log(f"   Checking {service_name}...", "INFO")
            
            start_time = time.time()
            while time.time() - start_time < max_wait:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        self.log(f"✅ {service_name} is ready", "PASS")
                        break
                except:
                    pass
                
                elapsed = int(time.time() - start_time)
                remaining = max_wait - elapsed
                if remaining > 0:
                    self.log(f"   {service_name}: Waiting... ({remaining}s)", "WAIT")
                    time.sleep(3)
                else:
                    self.log(f"⚠️  {service_name}: Not ready after {max_wait}s", "WARN")
                    break
    
    def show_status(self):
        """Show final status and URLs"""
        self.log("📊 Development environment status:", "INFO")
        
        try:
            # Show container status
            result = subprocess.run([
                'docker-compose', '-f', 'docker-compose.dev.yaml', 'ps'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.log("📦 Container Status:", "INFO")
                for line in result.stdout.split('\n'):
                    if line.strip() and 'NAME' not in line:
                        self.log(f"   {line}", "INFO")
            
        except Exception:
            pass
        
        self.log("", "INFO")
        self.log("🚀 Development URLs:", "INFO")
        self.log("   Frontend: http://localhost:3000", "INFO")
        self.log("   Backend:  http://localhost:8000", "INFO")
        self.log("   API Docs: http://localhost:8000/docs", "INFO")
        self.log("", "INFO")
        self.log("💡 Next Steps:", "INFO")
        self.log("   1. Open http://localhost:3000 in your browser", "INFO")
        self.log("   2. Hard refresh (Ctrl+Shift+R) to clear cache", "INFO")
        self.log("   3. Test with a YouTube URL", "INFO")
        self.log("   4. Check console for any remaining errors", "INFO")
    
    def start_development(self):
        """Main startup process"""
        self.log(f"🚀 STARTING DEVELOPMENT ENVIRONMENT - {self.timestamp}", "START")
        self.log("=" * 60, "INFO")
        
        # Step 1: Check or wait for Docker Desktop
        if not self.check_docker_desktop():
            self.log("🔧 Docker Desktop needs to be started", "INFO")
            self.log("   Please start Docker Desktop manually, then press Enter...", "INPUT")
            input()
            
            if not self.wait_for_docker():
                self.log("❌ Cannot proceed without Docker Desktop", "FAIL")
                return False
        
        # Step 2: Start containers
        if not self.start_containers():
            self.log("❌ Failed to start containers", "FAIL")
            return False
        
        # Step 3: Wait for services
        self.wait_for_services()
        
        # Step 4: Show status
        self.show_status()
        
        self.log("=" * 60, "INFO")
        self.log("✅ DEVELOPMENT ENVIRONMENT READY!", "SUCCESS")
        
        return True

if __name__ == "__main__":
    starter = DevelopmentStarter()
    success = starter.start_development()
    
    if not success:
        sys.exit(1) 