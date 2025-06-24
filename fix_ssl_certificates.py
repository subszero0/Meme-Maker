#!/usr/bin/env python3
"""
SSL Certificate Setup Script
============================

This script sets up SSL certificates for memeit.pro domain.
For production use, you should use Let's Encrypt or proper CA certificates.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n🔧 {description}")
    print(f"Command: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print(f"✅ Success: {description}")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Failed: {description}")
            print(f"Error: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏱️ Timeout: {description}")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def create_self_signed_certificates():
    """Create self-signed certificates for development/testing"""
    print("🔑 Creating self-signed SSL certificates...")
    
    # Create SSL directories
    os.makedirs("ssl/certs", exist_ok=True)
    os.makedirs("ssl/private", exist_ok=True)
    
    # Generate private key
    if not run_command(
        "openssl genrsa -out ssl/private/memeit.pro.key 2048",
        "Generate private key"
    ):
        return False
    
    # Generate certificate signing request
    csr_config = """[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = California
L = San Francisco
O = Meme Maker
CN = memeit.pro

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = memeit.pro
DNS.2 = www.memeit.pro
IP.1 = 13.126.173.223
"""
    
    with open("ssl/memeit.pro.conf", "w") as f:
        f.write(csr_config)
    
    # Generate certificate
    if not run_command(
        "openssl req -new -x509 -key ssl/private/memeit.pro.key -out ssl/certs/memeit.pro.crt -days 365 -config ssl/memeit.pro.conf -extensions v3_req",
        "Generate self-signed certificate"
    ):
        return False
    
    # Set proper permissions
    run_command("chmod 600 ssl/private/memeit.pro.key", "Set key permissions")
    run_command("chmod 644 ssl/certs/memeit.pro.crt", "Set certificate permissions")
    
    return True

def create_nginx_ssl_config():
    """Create nginx configuration with SSL"""
    ssl_config = """server {
    listen 80;
    listen [::]:80;
    server_name memeit.pro www.memeit.pro;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name memeit.pro www.memeit.pro;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/memeit.pro.crt;
    ssl_certificate_key /etc/ssl/private/memeit.pro.key;
    
    # SSL Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Root directory
    root /usr/share/nginx/html;
    index index.html index.htm;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            access_log off;
        }
    }

    # API proxy to backend
    location /api/ {
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
        
        # Timeouts
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

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }
}
"""
    
    with open("frontend-new/nginx-ssl.conf", "w") as f:
        f.write(ssl_config)
    
    print("✅ Created nginx SSL configuration")
    return True

def main():
    print("🔐 SSL CERTIFICATE SETUP")
    print("=" * 40)
    
    print("⚠️  Note: This creates self-signed certificates for testing.")
    print("   For production, use Let's Encrypt or proper CA certificates.")
    print()
    
    # Step 1: Create certificates
    if not create_self_signed_certificates():
        print("❌ Failed to create SSL certificates")
        return False
    
    # Step 2: Create nginx SSL config
    if not create_nginx_ssl_config():
        print("❌ Failed to create nginx SSL configuration")
        return False
    
    print("\n🎉 SSL SETUP COMPLETE!")
    print("=" * 40)
    print("✅ Self-signed certificates created")
    print("✅ Nginx SSL configuration ready")
    print()
    print("📋 Next Steps:")
    print("1. Run the localhost fix script first: python3 fix_production_localhost_issue.py")
    print("2. Copy nginx-ssl.conf to your frontend container")
    print("3. Restart services with SSL enabled")
    print()
    print("⚠️  Browser will show security warning for self-signed certificates")
    print("   Click 'Advanced' -> 'Proceed to memeit.pro' to bypass warning")
    
    return True

if __name__ == "__main__":
    if not Path("frontend-new").exists():
        print("❌ Error: Run this script from the project root directory")
        sys.exit(1)
    
    main() 