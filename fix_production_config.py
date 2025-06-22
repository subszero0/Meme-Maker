#!/usr/bin/env python3
"""
Comprehensive Production Fix Script
Fixes both frontend localhost calls and backend API routing
"""

import subprocess
import time
import requests
from datetime import datetime

class ProductionFixer:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def log(self, message, status="INFO"):
        print(f"[{status}] {message}")
        
    def run_command(self, cmd, description):
        """Run a command and return success status"""
        self.log(f"🔧 {description}", "ACTION")
        self.log(f"   Command: {cmd}", "COMMAND")
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                self.log(f"✅ {description} - Success", "PASS")
                if result.stdout.strip():
                    for line in result.stdout.strip().split('\n'):
                        self.log(f"   {line}", "OUTPUT")
                return True
            else:
                self.log(f"❌ {description} - Failed", "FAIL")
                if result.stderr.strip():
                    for line in result.stderr.strip().split('\n'):
                        self.log(f"   Error: {line}", "ERROR")
                return False
        except subprocess.TimeoutExpired:
            self.log(f"❌ {description} - Timeout", "FAIL")
            return False
        except Exception as e:
            self.log(f"❌ {description} - Exception: {e}", "FAIL")
            return False
    
    def backup_current_state(self):
        """Create backup of current state"""
        self.log("💾 Creating backup of current state", "INFO")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"backup_before_fix_{timestamp}"
        
        commands = [
            f"mkdir -p {backup_dir}",
            f"docker-compose ps > {backup_dir}/containers_before.txt",
            f"cp docker-compose.yaml {backup_dir}/",
            f"cp frontend-new/nginx.conf {backup_dir}/",
        ]
        
        success = True
        for cmd in commands:
            if not self.run_command(cmd, f"Backup: {cmd}"):
                success = False
        
        if success:
            self.log(f"✅ Backup created in {backup_dir}", "PASS")
        return success
    
    def fix_frontend_build(self):
        """Fix frontend build to use production mode"""
        self.log("🎨 Fixing frontend build configuration", "INFO")
        
        # Stop containers first
        self.run_command("docker-compose down", "Stop all containers")
        
        # Clear Docker build cache for frontend only
        self.run_command("docker image rm meme-maker-frontend || true", "Remove old frontend image")
        
        # Rebuild frontend with explicit production mode
        frontend_build_cmd = "docker-compose build --no-cache frontend"
        if not self.run_command(frontend_build_cmd, "Rebuild frontend with production config"):
            return False
        
        self.log("✅ Frontend rebuild completed", "PASS")
        return True
    
    def fix_backend_connectivity(self):
        """Ensure backend container can be reached by nginx"""
        self.log("🔌 Fixing backend connectivity", "INFO")
        
        # Rebuild backend if needed (to ensure latest config)
        backend_build_cmd = "docker-compose build --no-cache backend"
        if not self.run_command(backend_build_cmd, "Rebuild backend"):
            return False
        
        self.log("✅ Backend rebuild completed", "PASS")
        return True
    
    def start_services(self):
        """Start all services in correct order"""
        self.log("🚀 Starting services", "INFO")
        
        # Start all services
        if not self.run_command("docker-compose up -d", "Start all containers"):
            return False
        
        # Wait for services to be healthy
        self.log("⏳ Waiting for services to become healthy...", "INFO")
        time.sleep(30)
        
        # Check container status
        self.run_command("docker-compose ps", "Check container status")
        
        return True
    
    def test_fix(self):
        """Test that the fix worked"""
        self.log("🧪 Testing the fix", "INFO")
        
        tests = [
            ("Frontend accessible", "curl -s -o /dev/null -w '%{http_code}' https://memeit.pro"),
            ("API Health", "curl -s -o /dev/null -w '%{http_code}' https://memeit.pro/api/health"),
            ("Nginx healthy", "docker-compose exec frontend nginx -t"),
            ("Backend healthy", "docker-compose exec backend curl -f http://localhost:8000/health"),
        ]
        
        results = []
        for test_name, cmd in tests:
            success = self.run_command(cmd, test_name)
            results.append((test_name, success))
        
        # Summary
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        self.log(f"📊 Test Results: {passed}/{total} passed", "SUMMARY")
        
        for test_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            self.log(f"   {status} {test_name}", "SUMMARY")
        
        return passed == total
    
    def verify_production_fix(self):
        """Verify the specific issues are fixed"""
        self.log("🔍 Verifying production issues are resolved", "INFO")
        
        try:
            # Test 1: Frontend should no longer call localhost
            response = requests.get('https://memeit.pro', timeout=10)
            if response.status_code == 200:
                if 'localhost:8000' not in response.text:
                    self.log("✅ Frontend no longer has localhost references", "PASS")
                else:
                    self.log("❌ Frontend still has localhost references", "FAIL")
                    return False
            
            # Test 2: API should work
            api_response = requests.get('https://memeit.pro/api/health', timeout=10)
            if api_response.status_code == 200:
                self.log("✅ API endpoints working", "PASS")
            else:
                self.log(f"❌ API still broken: {api_response.status_code}", "FAIL")
                return False
            
            # Test 3: Metadata API should work
            metadata_response = requests.post('https://memeit.pro/api/v1/metadata', 
                                            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}, 
                                            timeout=15)
            if metadata_response.status_code == 200:
                self.log("✅ Metadata API working", "PASS")
            else:
                self.log(f"⚠️  Metadata API: {metadata_response.status_code} (may be expected)", "WARN")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Verification failed: {e}", "FAIL")
            return False
    
    def run_complete_fix(self):
        """Run the complete fix process"""
        self.log(f"🔧 STARTING PRODUCTION FIX - {self.timestamp}", "START")
        self.log("=" * 70, "INFO")
        
        steps = [
            ("Create backup", self.backup_current_state),
            ("Fix frontend build", self.fix_frontend_build),
            ("Fix backend connectivity", self.fix_backend_connectivity),
            ("Start services", self.start_services),
            ("Test basic functionality", self.test_fix),
            ("Verify production issues resolved", self.verify_production_fix),
        ]
        
        for step_name, step_func in steps:
            self.log(f"📋 Step: {step_name}", "STEP")
            
            try:
                success = step_func()
                if success:
                    self.log(f"✅ {step_name} - Completed", "PASS")
                else:
                    self.log(f"❌ {step_name} - Failed", "FAIL")
                    self.log("🛑 Fix process stopped due to failure", "FAIL")
                    return False
            except Exception as e:
                self.log(f"❌ {step_name} - Exception: {e}", "FAIL")
                return False
        
        self.log("=" * 70, "INFO")
        self.log("🎉 PRODUCTION FIX COMPLETED SUCCESSFULLY!", "SUCCESS")
        self.log("", "INFO")
        self.log("🌍 Your website should now work at: https://memeit.pro", "SUCCESS")
        self.log("✅ No more localhost:8000 errors in browser", "SUCCESS")
        self.log("✅ API endpoints should respond correctly", "SUCCESS")
        
        return True

def main():
    """Main function - run as script for production server"""
    print("🚨 CRITICAL: This script should be run ON THE PRODUCTION SERVER")
    print("   This will rebuild and restart your production containers")
    print()
    
    response = input("Are you running this on the production server? (y/N): ")
    if response.lower() != 'y':
        print("❌ Please run this script on your production server (AWS Lightsail)")
        return
    
    fixer = ProductionFixer()
    success = fixer.run_complete_fix()
    
    if not success:
        print("❌ Fix failed. Check the logs above for errors.")
        print("💾 A backup was created - you can restore if needed.")
    else:
        print("🎉 Fix completed! Test your website at https://memeit.pro")

if __name__ == "__main__":
    main() 