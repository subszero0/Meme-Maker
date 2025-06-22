#!/usr/bin/env python3
"""
Add Debug Logging to Running Frontend Container
"""

import subprocess
import sys
from datetime import datetime

def log(message, level="INFO"):
    """Enhanced logging with timestamps"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def inject_debug_script():
    """Inject debug logging script into the running container"""
    log("📝 Injecting debug logging into frontend container...")
    
    debug_script = '''
<!-- ENHANCED ERROR LOGGING FOR PRODUCTION DEBUGGING -->
<script>
    console.log("🔧 DEBUG LOGGING INITIALIZED");
    
    // 1. Global error handler
    window.addEventListener('error', function(event) {
        console.error('🚨 GLOBAL ERROR:', {
            message: event.message,
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno,
            stack: event.error ? event.error.stack : 'No stack trace',
            timestamp: new Date().toISOString()
        });
    });
    
    // 2. Unhandled promise rejection handler
    window.addEventListener('unhandledrejection', function(event) {
        console.error('🚨 UNHANDLED PROMISE REJECTION:', {
            reason: event.reason,
            promise: event.promise,
            timestamp: new Date().toISOString()
        });
    });
    
    // 3. Enhanced fetch wrapper with detailed logging
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        const url = args[0];
        const options = args[1] || {};
        
        console.log('🌐 API CALL INITIATED:', {
            url: url,
            method: options.method || 'GET',
            headers: options.headers || {},
            body: options.body ? 'Present' : 'None',
            timestamp: new Date().toISOString()
        });
        
        // Check for problematic URLs
        if (typeof url === 'string') {
            if (url.includes('/api/api/')) {
                console.error('🚨 DOUBLE API PREFIX DETECTED:', url);
                console.error('❌ This should be fixed - API calls should use single /api prefix');
            }
            if (url.includes('localhost:8000')) {
                console.error('🚨 LOCALHOST URL DETECTED:', url);
                console.error('❌ Production should use relative URLs, not localhost');
            }
            if (url.startsWith('/api/v1/')) {
                console.log('✅ CORRECT RELATIVE URL:', url);
            }
        }
        
        const startTime = performance.now();
        
        return originalFetch.apply(this, args)
            .then(response => {
                const endTime = performance.now();
                const duration = endTime - startTime;
                
                if (response.ok) {
                    console.log('✅ API SUCCESS:', {
                        url: url,
                        status: response.status,
                        statusText: response.statusText,
                        duration: Math.round(duration) + 'ms',
                        headers: Object.fromEntries(response.headers.entries()),
                        timestamp: new Date().toISOString()
                    });
                } else {
                    console.error('❌ API ERROR:', {
                        url: url,
                        status: response.status,
                        statusText: response.statusText,
                        duration: Math.round(duration) + 'ms',
                        headers: Object.fromEntries(response.headers.entries()),
                        timestamp: new Date().toISOString()
                    });
                }
                
                return response;
            })
            .catch(error => {
                const endTime = performance.now();
                const duration = endTime - startTime;
                
                console.error('🚨 NETWORK ERROR:', {
                    url: url,
                    error: error.message,
                    stack: error.stack,
                    duration: Math.round(duration) + 'ms',
                    timestamp: new Date().toISOString()
                });
                
                throw error;
            });
    };
    
    // 4. Log current configuration
    console.log('🔧 FRONTEND DEBUG INFO:', {
        userAgent: navigator.userAgent,
        url: window.location.href,
        timestamp: new Date().toISOString(),
        note: 'Watch for API calls in network tab'
    });
    
    // 5. Environment check
    setTimeout(() => {
        console.log('🔍 CONFIGURATION CHECK:');
        console.log('- API calls should be relative URLs like /api/v1/metadata');
        console.log('- NOT localhost:8000 URLs');
        console.log('- NOT double /api/api/ prefixes');
        console.log('- Check network tab for actual requests');
    }, 1000);
</script>
'''
    
    # Create a script file
    with open('debug_inject.html', 'w') as f:
        f.write(debug_script)
    
    try:
        # Copy the debug script to the container
        result = subprocess.run([
            'docker', 'cp', 'debug_inject.html', 
            'meme-maker-frontend:/tmp/debug_inject.html'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            log(f"❌ Failed to copy debug script: {result.stderr}")
            return False
        
        # Inject the script into the index.html
        inject_cmd = '''
            cd /usr/share/nginx/html && 
            cp index.html index.html.backup && 
            sed 's|</head>|<script>'"$(cat /tmp/debug_inject.html | grep -v '<script>' | grep -v '</script>')"'</script></head>|' index.html.backup > index.html
        '''
        
        result = subprocess.run([
            'docker', 'exec', 'meme-maker-frontend', 'sh', '-c', inject_cmd
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            log(f"❌ Failed to inject debug script: {result.stderr}")
            return False
        
        log("✅ Debug logging injected successfully")
        return True
        
    except Exception as e:
        log(f"❌ Exception during injection: {e}")
        return False
    
    finally:
        # Clean up temp file
        try:
            import os
            os.remove('debug_inject.html')
        except:
            pass

def main():
    """Main script"""
    log("🚀 ADDING DEBUG LOGGING TO RUNNING FRONTEND")
    log("=" * 60)
    
    # Step 1: Check if frontend is running
    log("\n🔍 Step 1: Check frontend status")
    result = subprocess.run(['docker', 'ps', '--filter', 'name=meme-maker-frontend'], 
                          capture_output=True, text=True)
    
    if 'meme-maker-frontend' not in result.stdout:
        log("❌ Frontend container not running")
        return False
    
    log("✅ Frontend container is running")
    
    # Step 2: Inject debug logging
    log("\n📝 Step 2: Inject debug logging")
    if not inject_debug_script():
        return False
    
    # Step 3: Test frontend accessibility
    log("\n🧪 Step 3: Test frontend")
    import requests
    try:
        response = requests.get('https://memeit.pro/debug', timeout=10)
        if response.status_code == 200:
            log("✅ Frontend accessible via https://memeit.pro/debug")
        else:
            log(f"⚠️  Frontend status: {response.status_code}")
    except Exception as e:
        log(f"⚠️  Frontend test failed: {e}")
    
    # Step 4: Final instructions
    log("\n🎯 FINAL INSTRUCTIONS:")
    log("=" * 60)
    log("🔥 CRITICAL NEXT STEPS:")
    log("1. Open https://memeit.pro in INCOGNITO/PRIVATE window")
    log("2. Open DevTools (F12) → Console tab")
    log("3. You should see: '🔧 DEBUG LOGGING INITIALIZED'")
    log("4. Enter a YouTube URL and click 'Let's Go!'")
    log("5. Watch for these messages:")
    log("   ✅ '🌐 API CALL INITIATED: /api/v1/metadata' (CORRECT)")
    log("   ❌ '🚨 DOUBLE API PREFIX DETECTED' (STILL BROKEN)")
    log("   ❌ '🚨 LOCALHOST URL DETECTED' (WRONG CONFIG)")
    log("6. Screenshot the console with the API call details")
    log("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 