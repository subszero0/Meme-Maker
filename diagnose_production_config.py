#!/usr/bin/env python3
"""
Diagnose Production Configuration Issue
Why is production frontend calling localhost:8000?
"""

import subprocess
import requests
import json
import time
from datetime import datetime

class ProductionDiagnostics:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def log(self, message, status="INFO"):
        print(f"[{status}] {message}")
        
    def test_production_server_status(self):
        """Check if production server containers are running"""
        self.log("🌍 Testing Production Server Status", "INFO")
        
        try:
            # Check if server containers are running (SSH or local if on server)
            self.log("   Attempting to check server container status...", "INFO")
            
            # Test API endpoint directly
            response = requests.get('https://memeit.pro/api/health', timeout=10)
            if response.status_code == 200:
                self.log("✅ Production backend is running and accessible", "PASS")
                return True
            else:
                self.log(f"❌ Production backend returned: {response.status_code}", "FAIL")
                return False
                
        except Exception as e:
            self.log(f"❌ Cannot reach production backend: {e}", "FAIL")
            return False
    
    def test_frontend_configuration(self):
        """Check what configuration the production frontend is actually using"""
        self.log("⚙️ Testing Frontend Configuration", "INFO")
        
        try:
            # Get the production frontend
            response = requests.get('https://memeit.pro', timeout=10)
            if response.status_code == 200:
                content = response.text
                
                # Look for configuration clues in the HTML/JS
                if 'localhost:8000' in content:
                    self.log("❌ FOUND: localhost:8000 hardcoded in frontend", "FAIL")
                    self.log("   This confirms the bug - production has development config", "FAIL")
                elif 'localhost' in content:
                    self.log("⚠️  Found localhost references (might be normal)", "WARN")
                else:
                    self.log("✅ No obvious localhost references in HTML", "PASS")
                
                # Check for environment indicators
                if 'NODE_ENV=production' in content or 'production' in content.lower():
                    self.log("✅ Found production environment indicators", "PASS")
                else:
                    self.log("⚠️  No clear production environment indicators", "WARN")
                
                return True
            else:
                self.log(f"❌ Cannot fetch frontend: {response.status_code}", "FAIL")
                return False
                
        except Exception as e:
            self.log(f"❌ Frontend test failed: {e}", "FAIL")
            return False
    
    def test_api_routing(self):
        """Test if nginx is properly routing API calls"""
        self.log("🔗 Testing API Routing", "INFO")
        
        # Test the routes that should work
        endpoints = [
            ('https://memeit.pro/api/health', 'API Health'),
            ('https://memeit.pro/api/v1/metadata', 'Metadata API')
        ]
        
        for url, name in endpoints:
            try:
                if 'metadata' in url:
                    response = requests.post(url, 
                                           json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}, 
                                           timeout=10)
                else:
                    response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    self.log(f"✅ {name}: Working ({response.status_code})", "PASS")
                else:
                    self.log(f"❌ {name}: Failed ({response.status_code})", "FAIL")
                    
            except Exception as e:
                self.log(f"❌ {name}: Error - {e}", "FAIL")
    
    def analyze_build_issue(self):
        """Analyze potential build configuration issues"""
        self.log("🔍 Analyzing Build Configuration Issues", "INFO")
        
        # Check if we can identify the issue
        issues = [
            "1. Vite build not setting MODE=production correctly",
            "2. Environment detection logic failing in browser",
            "3. Docker build caching old development config",
            "4. Frontend container built with wrong environment",
        ]
        
        self.log("🎯 Potential root causes:", "INFO")
        for issue in issues:
            self.log(f"   {issue}", "INFO")
        
        self.log("", "INFO")
        self.log("🔧 Recommended fixes:", "INFO")
        self.log("   1. Rebuild frontend with explicit production env", "ACTION")
        self.log("   2. Clear Docker build cache", "ACTION")
        self.log("   3. Verify Vite production build output", "ACTION")
        self.log("   4. Redeploy with fresh container images", "ACTION")
    
    def provide_fix_commands(self):
        """Provide specific commands to fix the issue"""
        self.log("🛠️ Fix Commands (Run on Production Server)", "ACTION")
        
        commands = [
            "# Stop containers",
            "docker-compose down",
            "",
            "# Clear build cache", 
            "docker system prune -a --volumes",
            "",
            "# Rebuild frontend with explicit production env",
            "docker-compose build --no-cache frontend",
            "",
            "# Start containers",
            "docker-compose up -d",
            "",
            "# Verify containers",
            "docker-compose ps",
            "",
            "# Test the fix",
            "curl https://memeit.pro/api/health"
        ]
        
        for cmd in commands:
            if cmd.startswith("#"):
                self.log(cmd, "COMMENT")
            elif cmd == "":
                self.log("", "INFO")
            else:
                self.log(f"   {cmd}", "COMMAND")
    
    def run_diagnosis(self):
        """Run complete diagnosis"""
        self.log(f"🔍 PRODUCTION CONFIGURATION DIAGNOSIS - {self.timestamp}", "START")
        self.log("=" * 60, "INFO")
        
        # Run diagnostic tests
        server_ok = self.test_production_server_status()
        frontend_ok = self.test_frontend_configuration()
        self.test_api_routing()
        
        self.log("=" * 60, "INFO")
        self.log("📊 DIAGNOSIS SUMMARY", "SUMMARY")
        
        if server_ok and not frontend_ok:
            self.log("❌ CONFIRMED: Frontend configuration bug", "SUMMARY")
            self.log("   Backend working, frontend calling localhost", "SUMMARY")
        elif not server_ok:
            self.log("❌ Server-side issues detected", "SUMMARY")
        else:
            self.log("⚠️  Mixed results - need manual investigation", "SUMMARY")
        
        self.analyze_build_issue()
        self.provide_fix_commands()

if __name__ == "__main__":
    diagnostics = ProductionDiagnostics()
    diagnostics.run_diagnosis() 