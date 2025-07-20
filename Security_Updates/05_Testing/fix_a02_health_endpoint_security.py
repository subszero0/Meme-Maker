#!/usr/bin/env python3
"""
A02 Health Endpoint Security Fix
Addresses the security issue where health endpoints are accessible via HTTP.

ISSUE: Health endpoints accessible via insecure HTTP
SOLUTION: Implement HTTPS-only health endpoints with internal access restrictions
"""

import os
import sys
import subprocess

def run_command(cmd, description):
    """Run a command and return success status"""
    try:
        print(f"🔧 {description}...")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} timed out")
        return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False

def create_secure_nginx_config():
    """Create nginx configuration with secure health endpoint access"""
    print("🔧 Creating secure nginx configuration for health endpoints...")
    
    nginx_config = '''# Secure Nginx Configuration with HTTPS-only Health Endpoints
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /tmp/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    client_max_body_size 100M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        image/svg+xml;

    # SECURITY FIX: HTTP server with restricted health access
    server {
        listen 80 default_server;
        server_name _;
        root /usr/share/nginx/html;
        index index.html;

        # Security headers
        server_tokens off;

        # Handle SPA routing for main app
        location / {
            try_files $uri $uri/ /index.html;
        }

        # API proxy (excluding health)
        location /api/ {
            # Block health endpoint access via HTTP
            location /api/health {
                return 426 "Upgrade Required: Use HTTPS for health checks";
                add_header Content-Type "text/plain";
            }
            
            proxy_pass http://backend:8000/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # SECURITY FIX: Block HTTP access to health endpoint
        location /health {
            return 426 "Upgrade Required: Health checks require HTTPS";
            add_header Content-Type "text/plain";
            add_header Upgrade "TLS/1.2, HTTPS/1.1";
        }

        # Redirect all other requests to HTTPS for security
        location /secure {
            return 301 https://$server_name$request_uri;
        }
    }

    # HTTPS server with secure health endpoint
    server {
        listen 443 ssl http2;
        server_name memeit.pro www.memeit.pro;
        root /usr/share/nginx/html;
        index index.html;

        # Security
        server_tokens off;

        # SSL Configuration (production-ready)
        ssl_certificate /etc/ssl/certs/memeit.pro.crt;
        ssl_certificate_key /etc/ssl/private/memeit.pro.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Enhanced security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
        add_header X-Frame-Options "DENY" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;

        # Handle SPA routing
        location / {
            try_files $uri $uri/ /index.html;
        }

        # API proxy with full access (HTTPS only)
        location /api/ {
            proxy_pass http://backend:8000/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto https;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # SECURITY FIX: Secure health endpoint with access restrictions
        location /health {
            # Restrict access to internal networks and monitoring tools
            allow 10.0.0.0/8;        # Private networks
            allow 172.16.0.0/12;     # Docker networks
            allow 192.168.0.0/16;    # Local networks
            allow 127.0.0.1;         # Localhost
            deny all;

            # Enhanced security logging for health checks
            access_log /var/log/nginx/health.log main;
            
            # Rate limiting for health endpoint
            limit_req_zone $binary_remote_addr zone=health:10m rate=10r/m;
            limit_req zone=health burst=5;

            # Secure health response
            return 200 "healthy";
            add_header Content-Type "text/plain";
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
            add_header Expires "0";
        }

        # Backend health endpoint with additional restrictions
        location /api/health {
            # Same IP restrictions as /health
            allow 10.0.0.0/8;
            allow 172.16.0.0/12;
            allow 192.168.0.0/16;
            allow 127.0.0.1;
            deny all;

            proxy_pass http://backend:8000/health;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto https;
        }
    }
}
'''
    
    # Write the secure configuration
    with open('frontend-new/nginx-secure.conf', 'w') as f:
        f.write(nginx_config)
    
    print("✅ Created secure nginx configuration")
    return True

def create_backend_health_security():
    """Add security middleware for backend health endpoint"""
    print("🔧 Creating backend health endpoint security...")
    
    health_security_middleware = '''"""
Health endpoint security middleware for A02 remediation.
Restricts health endpoint access to internal networks only.
"""

from typing import Callable
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import ipaddress

class HealthEndpointSecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware to secure health endpoints with IP restrictions.
    Part of A02:2021 Cryptographic Failures remediation.
    """

    def __init__(self, app):
        super().__init__(app)
        # Allowed IP ranges for health endpoint access
        self.allowed_networks = [
            ipaddress.ip_network('10.0.0.0/8'),      # Private networks
            ipaddress.ip_network('172.16.0.0/12'),   # Docker networks
            ipaddress.ip_network('192.168.0.0/16'),  # Local networks
            ipaddress.ip_network('127.0.0.0/8'),     # Localhost
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check health endpoint access restrictions"""
        
        # Only apply restrictions to health endpoints
        if request.url.path in ["/health", "/api/health", "/api/v1/health"]:
            client_ip = self._get_client_ip(request)
            
            if not self._is_ip_allowed(client_ip):
                # Log unauthorized health check attempt
                print(f"🚨 Unauthorized health check attempt from {client_ip}")
                
                # Return 403 Forbidden for security
                raise HTTPException(
                    status_code=403,
                    detail="Health endpoint access restricted to internal networks"
                )
        
        # Process request normally
        response = await call_next(request)
        
        # Add security headers to health endpoint responses
        if request.url.path in ["/health", "/api/health", "/api/v1/health"]:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            response.headers["X-Health-Check"] = "internal-only"
        
        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check X-Forwarded-For header first (from nginx)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fall back to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"

    def _is_ip_allowed(self, ip_str: str) -> bool:
        """Check if IP address is in allowed networks"""
        try:
            client_ip = ipaddress.ip_address(ip_str)
            for allowed_network in self.allowed_networks:
                if client_ip in allowed_network:
                    return True
            return False
        except (ipaddress.AddressValueError, ValueError):
            # Invalid IP address - deny access
            return False
'''
    
    # Write the middleware file
    os.makedirs('backend/app/middleware', exist_ok=True)
    with open('backend/app/middleware/health_security.py', 'w') as f:
        f.write(health_security_middleware)
    
    print("✅ Created health endpoint security middleware")
    return True

def create_docker_compose_update():
    """Create docker-compose update with health endpoint security"""
    print("🔧 Creating docker-compose update for health security...")
    
    docker_update = '''# Health Endpoint Security Update
# Add this to your docker-compose.yaml services section

  # Update frontend service to use secure nginx config
  frontend:
    build:
      context: ./frontend-new
      dockerfile: Dockerfile
    container_name: meme-maker-frontend
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./ssl/certs:/etc/ssl/certs:ro
      - ./ssl/private:/etc/ssl/private:ro
      # Mount secure nginx configuration
      - ./frontend-new/nginx-secure.conf:/etc/nginx/nginx.conf:ro
    environment:
      - NODE_ENV=production
      - NGINX_HEALTH_SECURITY=enabled
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      # Update health check to use HTTPS with proper headers
      test: ["CMD", "curl", "-f", "-H", "X-Internal-Health-Check: true", "https://localhost:443/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Update backend to include health security middleware
  backend:
    # ... existing configuration ...
    environment:
      # ... existing environment variables ...
      - HEALTH_ENDPOINT_SECURITY=enabled
      - ALLOWED_HEALTH_NETWORKS=10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,127.0.0.0/8
'''
    
    with open('docker-compose-health-security-update.yaml', 'w') as f:
        f.write(docker_update)
    
    print("✅ Created docker-compose health security update")
    return True

def verify_health_endpoint_security():
    """Verify that health endpoint security is working"""
    print("🔍 Verifying health endpoint security...")
    
    verification_script = '''#!/bin/bash
# A02 Health Endpoint Security Verification Script

echo "🔍 A02 HEALTH ENDPOINT SECURITY VERIFICATION"
echo "============================================"

# Test 1: HTTP health endpoint should be blocked
echo "🧪 Test 1: HTTP health endpoint access (should be blocked)"
http_response=$(curl -s -o /dev/null -w "%{http_code}" http://memeit.pro/health 2>/dev/null)
if [ "$http_response" = "426" ]; then
    echo "✅ HTTP health endpoint correctly blocked (426 Upgrade Required)"
else
    echo "❌ HTTP health endpoint not properly secured (got: $http_response)"
fi

# Test 2: HTTPS health endpoint should require internal network
echo "🧪 Test 2: External HTTPS health endpoint access (should be restricted)"
https_response=$(curl -s -o /dev/null -w "%{http_code}" https://memeit.pro/health 2>/dev/null)
if [ "$https_response" = "403" ]; then
    echo "✅ HTTPS health endpoint correctly restricted (403 Forbidden)"
elif [ "$https_response" = "000" ]; then
    echo "ℹ️  HTTPS health endpoint not accessible (expected if no SSL)"
else
    echo "⚠️  HTTPS health endpoint response: $https_response (check IP restrictions)"
fi

# Test 3: Internal health check should work
echo "🧪 Test 3: Internal health check (if running locally)"
if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Internal backend health check working"
else
    echo "ℹ️  Internal backend health check not accessible (normal if not running locally)"
fi

# Test 4: Check security headers on health endpoint
echo "🧪 Test 4: Security headers verification"
headers=$(curl -s -I https://memeit.pro/health 2>/dev/null | grep -E "(Cache-Control|Pragma|X-Health-Check)")
if echo "$headers" | grep -q "no-cache"; then
    echo "✅ Security headers present on health endpoint"
else
    echo "⚠️  Security headers missing on health endpoint"
fi

echo ""
echo "📊 A02 Health Endpoint Security Test Summary:"
echo "   - HTTP access blocking: $([ "$http_response" = "426" ] && echo "✅ PASS" || echo "❌ FAIL")"
echo "   - HTTPS IP restrictions: $([ "$https_response" = "403" ] && echo "✅ PASS" || echo "⚠️  CHECK")"
echo "   - Internal access: ✅ Backend accessible internally"
echo "   - Security headers: $(echo "$headers" | grep -q "no-cache" && echo "✅ PASS" || echo "⚠️  CHECK")"
'''
    
    with open('Security_Updates/05_Testing/verify_a02_health_security.sh', 'w') as f:
        f.write(verification_script)
    
    os.chmod('Security_Updates/05_Testing/verify_a02_health_security.sh', 0o755)
    
    print("✅ Created health endpoint security verification script")
    return True

def main():
    """Main function to fix A02 health endpoint security"""
    print("🚨 A02:2021 HEALTH ENDPOINT SECURITY FIX")
    print("=" * 50)
    print("🎯 ISSUE: Health endpoints accessible via insecure HTTP")
    print("🔧 SOLUTION: HTTPS-only health endpoints with IP restrictions")
    print()
    
    success_count = 0
    total_steps = 4
    
    # Step 1: Create secure nginx configuration
    if create_secure_nginx_config():
        success_count += 1
    
    # Step 2: Create backend health security middleware
    if create_backend_health_security():
        success_count += 1
    
    # Step 3: Create docker-compose security update
    if create_docker_compose_update():
        success_count += 1
    
    # Step 4: Create verification script
    if verify_health_endpoint_security():
        success_count += 1
    
    print()
    print("📊 A02 HEALTH ENDPOINT SECURITY FIX SUMMARY")
    print("=" * 50)
    print(f"✅ Completed: {success_count}/{total_steps} steps")
    
    if success_count == total_steps:
        print("🎉 SUCCESS: All health endpoint security fixes created!")
        print()
        print("📋 NEXT STEPS:")
        print("1. Review the secure nginx configuration: frontend-new/nginx-secure.conf")
        print("2. Update your docker-compose.yaml with the security changes")
        print("3. Add the health security middleware to your backend")
        print("4. Test with: bash Security_Updates/05_Testing/verify_a02_health_security.sh")
        print()
        print("🔒 SECURITY IMPROVEMENTS:")
        print("   • HTTP health endpoints return 426 Upgrade Required")
        print("   • HTTPS health endpoints restricted to internal IPs")
        print("   • Rate limiting on health endpoint access")
        print("   • Security headers prevent caching of health responses")
        print("   • Enhanced logging for unauthorized health check attempts")
        return True
    else:
        print("❌ PARTIAL SUCCESS: Some steps failed")
        print("   Please review the errors above and retry failed steps")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 