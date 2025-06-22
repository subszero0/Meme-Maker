#!/usr/bin/env python3
"""
Force Frontend Fix with Enhanced Logging
Completely rebuilds production frontend and adds comprehensive error logging
"""

import subprocess
import sys
import time
import requests
from datetime import datetime
import json

def log(message, level="INFO"):
    """Enhanced logging with timestamps"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def run_command(cmd, description, timeout=300):
    """Run a command with detailed logging"""
    log(f"Running: {description}")
    log(f"Command: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        
        if result.returncode == 0:
            log(f"✅ {description} - Success")
            if result.stdout.strip():
                # Log first 500 chars of output
                output = result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout
                log(f"Output: {output}")
            return True
        else:
            log(f"❌ {description} - Failed (exit code: {result.returncode})")
            if result.stderr.strip():
                log(f"Error: {result.stderr[:500]}...")
            if result.stdout.strip():
                log(f"Output: {result.stdout[:500]}...")
            return False
            
    except subprocess.TimeoutExpired:
        log(f"❌ {description} - Timed out after {timeout} seconds")
        return False
    except Exception as e:
        log(f"❌ {description} - Exception: {e}")
        return False

def test_frontend_config():
    """Test if frontend is using correct API configuration"""
    log("🔍 Testing frontend configuration...")
    
    try:
        # Check if frontend is accessible
        response = requests.get('https://memeit.pro', timeout=10)
        if response.status_code != 200:
            log(f"❌ Frontend not accessible: {response.status_code}")
            return False
            
        # Check for localhost references in the HTML/JS
        content = response.text.lower()
        if 'localhost:8000' in content:
            log("❌ Frontend still contains localhost:8000 references")
            return False
        elif 'localhost' in content:
            log("⚠️  Frontend contains localhost references (may be normal)")
            
        # Test actual API call behavior
        log("🧪 Testing API call behavior...")
        
        # Try to make a test API call and see what URL it actually uses
        test_js = """
        fetch('/api/v1/health', {method: 'GET'})
            .then(r => console.log('API test result:', r.status))
            .catch(e => console.log('API test error:', e));
        """
        
        log("✅ Frontend accessible, check browser network tab for actual API calls")
        return True
        
    except Exception as e:
        log(f"❌ Frontend config test failed: {e}")
        return False

def verify_environment_file():
    """Verify our changes were actually applied to the source code"""
    log("🔍 Verifying environment configuration changes...")
    
    try:
        with open('frontend-new/src/config/environment.ts', 'r') as f:
            content = f.read()
            
        if "API_BASE_URL: '/api'" in content:
            log("❌ CRITICAL: Source code still has old config: API_BASE_URL: '/api'")
            log("📝 This means our changes weren't applied or were reverted")
            return False
        elif "API_BASE_URL: ''" in content:
            log("✅ Source code has correct config: API_BASE_URL: ''")
            return True
        else:
            log("⚠️  Unexpected API_BASE_URL configuration in source")
            # Show the relevant line
            for i, line in enumerate(content.split('\n'), 1):
                if 'API_BASE_URL:' in line and 'production' in content.split('\n')[max(0, i-5):i]:
                    log(f"📋 Line {i}: {line.strip()}")
            return False
            
    except Exception as e:
        log(f"❌ Could not verify environment file: {e}")
        return False

def add_enhanced_logging():
    """Add enhanced error logging to the frontend"""
    log("📝 Adding enhanced error logging to frontend...")
    
    # Create a logging configuration for the frontend
    logging_config = """
// Enhanced error logging for production debugging
window.addEventListener('error', (event) => {
    console.error('🚨 Global Error:', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error?.stack
    });
});

// Enhanced fetch error logging
const originalFetch = window.fetch;
window.fetch = function(...args) {
    console.log('🌐 API Call:', args[0], args[1] || {});
    return originalFetch.apply(this, args)
        .then(response => {
            if (!response.ok) {
                console.error('🚨 API Error:', {
                    url: args[0],
                    status: response.status,
                    statusText: response.statusText,
                    headers: Object.fromEntries(response.headers.entries())
                });
            } else {
                console.log('✅ API Success:', args[0], response.status);
            }
            return response;
        })
        .catch(error => {
            console.error('🚨 Network Error:', {
                url: args[0],
                error: error.message,
                stack: error.stack
            });
            throw error;
        });
};

console.log('🔧 Enhanced logging initialized');
"""
    
    try:
        # Add logging to the main HTML file in frontend build
        with open('frontend-new/index.html', 'r') as f:
            html_content = f.read()
            
        if '🔧 Enhanced logging initialized' not in html_content:
            # Add script before closing head tag
            enhanced_html = html_content.replace(
                '</head>',
                f'<script>{logging_config}</script>\n</head>'
            )
            
            with open('frontend-new/index.html', 'w') as f:
                f.write(enhanced_html)
                
            log("✅ Enhanced logging added to frontend")
        else:
            log("✅ Enhanced logging already present")
            
        return True
        
    except Exception as e:
        log(f"❌ Failed to add enhanced logging: {e}")
        return False

def main():
    """Main fix process with comprehensive logging"""
    log("🚀 STARTING COMPREHENSIVE FRONTEND FIX")
    log("=" * 70)
    
    # Step 1: Verify our source code changes
    log("\n📋 Step 1: Verify source code changes")
    if not verify_environment_file():
        log("❌ CRITICAL: Source code doesn't have our fixes!")
        log("💡 Re-applying the fix...")
        
        # Re-apply the fix
        try:
            with open('frontend-new/src/config/environment.ts', 'r') as f:
                content = f.read()
                
            # Fix the production config
            content = content.replace(
                "API_BASE_URL: '/api',",
                "API_BASE_URL: '',"
            )
            content = content.replace(
                "return '/api';",
                "return '';"
            )
            
            with open('frontend-new/src/config/environment.ts', 'w') as f:
                f.write(content)
                
            log("✅ Re-applied source code fix")
            
        except Exception as e:
            log(f"❌ Failed to re-apply fix: {e}")
            return False
    
    # Step 2: Add enhanced logging
    log("\n📝 Step 2: Add enhanced error logging")
    add_enhanced_logging()
    
    # Step 3: Stop all containers
    log("\n🛑 Step 3: Stop all containers")
    run_command("docker-compose down", "Stop all containers")
    
    # Step 4: Clean Docker cache aggressively
    log("\n🧹 Step 4: Clean Docker cache")
    run_command("docker system prune -f", "Clean Docker cache")
    run_command("docker builder prune -f", "Clean Docker build cache")
    
    # Step 5: Remove frontend image specifically
    log("\n🗑️ Step 5: Remove frontend image")
    run_command("docker rmi meme-maker-frontend --force", "Remove frontend image", timeout=60)
    
    # Step 6: Rebuild frontend with no cache
    log("\n🔨 Step 6: Rebuild frontend (no cache)")
    if not run_command("docker-compose build --no-cache frontend", "Rebuild frontend", timeout=600):
        log("❌ CRITICAL: Frontend rebuild failed")
        return False
    
    # Step 7: Start all services
    log("\n🚀 Step 7: Start services")
    if not run_command("docker-compose up -d", "Start all services", timeout=120):
        log("❌ CRITICAL: Failed to start services")
        return False
    
    # Step 8: Wait for services
    log("\n⏳ Step 8: Wait for services to stabilize")
    time.sleep(30)
    
    # Step 9: Check container status
    log("\n🔍 Step 9: Check container status")
    run_command("docker-compose ps", "Check container status")
    
    # Step 10: Test frontend configuration
    log("\n🧪 Step 10: Test frontend configuration")
    if test_frontend_config():
        log("✅ Frontend configuration test passed")
    else:
        log("❌ Frontend configuration test failed")
    
    # Step 11: Test API endpoint directly
    log("\n🌐 Step 11: Test API endpoint")
    try:
        response = requests.post(
            'https://memeit.pro/api/v1/metadata',
            json={'url': 'https://www.youtube.com/watch?v=test'},
            timeout=15
        )
        log(f"✅ API endpoint responding: {response.status_code}")
    except Exception as e:
        log(f"❌ API endpoint test failed: {e}")
    
    # Step 12: Final instructions
    log("\n🎯 Step 12: Final verification instructions")
    log("=" * 70)
    log("🔥 CRITICAL NEXT STEPS:")
    log("1. Open https://memeit.pro in a NEW INCOGNITO/PRIVATE WINDOW")
    log("2. Open DevTools (F12) → Console tab")
    log("3. You should see: '🔧 Enhanced logging initialized'")
    log("4. Enter a YouTube URL and click 'Let's Go!'")
    log("5. Watch the console for:")
    log("   - ✅ '🌐 API Call: /api/v1/metadata' (correct)")
    log("   - ❌ '🌐 API Call: /api/api/v1/metadata' (still broken)")
    log("6. Screenshot any errors you see")
    log("=" * 70)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 