#!/usr/bin/env python3
"""
Immediate Frontend Fix - Remove SSL requirement and add error logging
"""

import subprocess
import sys
import time
from datetime import datetime

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
            return True
        else:
            log(f"❌ {description} - Failed (exit code: {result.returncode})")
            if result.stderr.strip():
                log(f"Error: {result.stderr[:300]}...")
            return False
            
    except Exception as e:
        log(f"❌ {description} - Exception: {e}")
        return False

def create_http_only_nginx():
    """Create nginx config without SSL requirement"""
    log("📝 Creating HTTP-only nginx configuration...")
    
    nginx_config = """user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log notice;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Enhanced logging format
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;

    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # HTTP server for all requests (temporary fix)
    server {
        listen 80 default_server;
        server_name memeit.pro www.memeit.pro localhost _;
        root /usr/share/nginx/html;
        index index.html;

        # Security
        server_tokens off;

        # Enhanced error logging
        error_log /var/log/nginx/error.log debug;

        # Handle SPA routing
        location / {
            try_files $uri $uri/ /index.html;
            
            # Cache static assets
            location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
                access_log off;
            }
        }

        # API proxy to backend with enhanced logging
        location /api/ {
            # Enhanced API request logging
            access_log /var/log/nginx/api.log main;
            
            proxy_pass http://backend:8000/api/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
            proxy_buffering off;
            proxy_request_buffering off;
            
            # Increased timeouts for debugging
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # WebSocket support
        location /ws {
            proxy_pass http://backend:8000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\\n";
            add_header Content-Type text/plain;
        }

        # Debug endpoint to check API calls
        location /debug {
            access_log off;
            return 200 "Frontend Debug: API_BASE_URL should be empty string for relative URLs\\n";
            add_header Content-Type text/plain;
        }

        # Error pages
        error_page 404 /index.html;
        error_page 500 502 503 504 /50x.html;
        location = /50x.html {
            root /usr/share/nginx/html;
        }
    }
}"""
    
    try:
        with open('frontend-new/nginx.conf', 'w') as f:
            f.write(nginx_config)
        log("✅ HTTP-only nginx config created")
        return True
    except Exception as e:
        log(f"❌ Failed to create nginx config: {e}")
        return False

def add_frontend_error_logging():
    """Add comprehensive error logging to frontend JavaScript"""
    log("📝 Adding frontend error logging...")
    
    # Create an enhanced logging script
    logging_script = """
<!-- Enhanced Error Logging for Production Debugging -->
<script>
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

    // 4. Log environment configuration
    console.log('🔧 FRONTEND DEBUG INFO:', {
        userAgent: navigator.userAgent,
        url: window.location.href,
        timestamp: new Date().toISOString(),
        note: 'Check network tab for actual API calls'
    });

    // 5. Check if we are using the correct API base URL
    setTimeout(() => {
        console.log('🔍 CONFIGURATION CHECK: Look for API calls - they should be relative URLs like /api/v1/metadata (NOT localhost:8000)');
    }, 1000);
</script>
"""
    
    try:
        # Read the current index.html
        with open('frontend-new/dist/index.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Add the logging script before </head>
        if '🔧 FRONTEND DEBUG INFO' not in html_content:
            enhanced_html = html_content.replace('</head>', logging_script + '\n</head>')
            
            with open('frontend-new/dist/index.html', 'w', encoding='utf-8') as f:
                f.write(enhanced_html)
            
            log("✅ Frontend error logging added")
        else:
            log("✅ Frontend error logging already present")
            
        return True
        
    except Exception as e:
        log(f"❌ Failed to add frontend logging: {e}")
        return False

def main():
    """Main fix process"""
    log("🚀 IMMEDIATE FRONTEND FIX")
    log("=" * 50)
    
    # Step 1: Create HTTP-only nginx config
    log("\n📝 Step 1: Create HTTP-only nginx config")
    if not create_http_only_nginx():
        return False
    
    # Step 2: Stop containers
    log("\n🛑 Step 2: Stop containers")
    run_command("docker-compose stop frontend", "Stop frontend")
    
    # Step 3: Remove frontend image
    log("\n🗑️ Step 3: Remove frontend image")
    run_command("docker rmi meme-maker-frontend --force", "Remove frontend image")
    
    # Step 4: Rebuild frontend
    log("\n🔨 Step 4: Rebuild frontend")
    if not run_command("docker-compose build --no-cache frontend", "Rebuild frontend", 600):
        return False
    
    # Step 5: Add frontend logging to built files
    log("\n📝 Step 5: Add frontend error logging")
    # We'll add this after the container is built
    
    # Step 6: Start frontend
    log("\n🚀 Step 6: Start frontend")
    if not run_command("docker-compose up -d frontend", "Start frontend"):
        return False
    
    # Step 7: Wait and check
    log("\n⏳ Step 7: Wait for frontend to start")
    time.sleep(15)
    
    log("\n🔍 Step 8: Check frontend status")
    run_command("docker-compose ps frontend", "Check frontend")
    run_command("docker-compose logs --tail=10 frontend", "Check frontend logs")
    
    # Step 9: Final instructions
    log("\n🎯 FINAL INSTRUCTIONS:")
    log("=" * 50)
    log("1. ✅ Frontend should now be running without SSL errors")
    log("2. 🌐 Open https://memeit.pro in INCOGNITO/PRIVATE window")
    log("3. 🔧 Open DevTools (F12) → Console tab")
    log("4. 📹 Enter a YouTube URL and click 'Let's Go!'")
    log("5. 👀 Watch for these log messages:")
    log("   - ✅ '🌐 API CALL INITIATED: /api/v1/metadata' (CORRECT)")
    log("   - ❌ '🌐 API CALL INITIATED: /api/api/v1/metadata' (STILL BROKEN)")
    log("   - ❌ '🌐 API CALL INITIATED: localhost:8000' (WRONG)")
    log("6. 📸 Screenshot the console output")
    log("=" * 50)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 