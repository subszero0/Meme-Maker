#!/usr/bin/env python3
"""
Fix Nginx Configuration Properly
Addresses the corrupted nginx config from previous attempt
"""

import os
import subprocess
import time

def backup_current_config():
    """Create backup of current config"""
    print("📋 Creating backup of current nginx config...")
    if os.path.exists('frontend-new/nginx.conf'):
        subprocess.run(['cp', 'frontend-new/nginx.conf', 'frontend-new/nginx.conf.corrupted'])
        print("✅ Backup created: nginx.conf.corrupted")
    else:
        print("⚠️  No nginx.conf found to backup")

def create_working_nginx_config():
    """Create a complete working nginx configuration"""
    print("🔧 Creating working nginx configuration...")
    
    nginx_config = """events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Basic settings
    sendfile on;
    tcp_nopush on;
    keepalive_timeout 65;
    
    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;
    
    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # HTTP server (without SSL for now)
    server {
        listen 80;
        server_name localhost memeit.pro www.memeit.pro _;
        root /usr/share/nginx/html;
        index index.html;

        # Health check endpoint
        location = /health {
            access_log off;
            return 200 "healthy\\n";
            add_header Content-Type text/plain;
        }

        # Handle SPA routing
        location / {
            try_files $uri $uri/ /index.html;
        }

        # API health endpoint fix - proxy /api/health to /health
        location = /api/health {
            proxy_pass http://backend:8000/health;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # All other API calls
        location /api/ {
            proxy_pass http://backend:8000/api/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # CORS headers
            add_header Access-Control-Allow-Origin "*" always;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
            add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
            
            # Handle preflight requests
            if ($request_method = 'OPTIONS') {
                return 204;
            }
        }
    }
}"""

    # Write the config
    with open('frontend-new/nginx.conf', 'w') as f:
        f.write(nginx_config)
    
    print("✅ nginx.conf created successfully")

def fix_docker_compose_ports():
    """Fix Docker Compose port mapping"""
    print("🔧 Fixing Docker Compose port mapping...")
    
    try:
        # Read current docker-compose.yaml
        with open('docker-compose.yaml', 'r') as f:
            content = f.read()
        
        # Fix port mapping - ensure it's 80:80 not 80:3000
        if '80:3000' in content:
            content = content.replace('80:3000', '80:80')
            print("✅ Fixed port mapping: 80:3000 → 80:80")
        elif '80:80' in content:
            print("✅ Port mapping already correct: 80:80")
        else:
            print("⚠️  No standard port mapping found")
        
        # Write back the file
        with open('docker-compose.yaml', 'w') as f:
            f.write(content)
            
    except Exception as e:
        print(f"❌ Error fixing docker-compose.yaml: {e}")

def test_nginx_config():
    """Test nginx configuration syntax"""
    print("🧪 Testing nginx configuration syntax...")
    
    try:
        result = subprocess.run([
            'docker', 'run', '--rm', 
            '-v', f'{os.getcwd()}/frontend-new/nginx.conf:/etc/nginx/nginx.conf:ro',
            'nginx:alpine', 'nginx', '-t'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ nginx configuration syntax is valid")
            return True
        else:
            print("❌ nginx configuration syntax error:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"⚠️  Could not test nginx config: {e}")
        return None

def rebuild_frontend():
    """Rebuild frontend container"""
    print("🔨 Rebuilding frontend container...")
    
    # Stop current frontend
    subprocess.run(['docker-compose', 'stop', 'frontend'], timeout=30)
    
    # Remove the problematic container
    subprocess.run(['docker-compose', 'rm', '-f', 'frontend'], timeout=30)
    
    # Build new container
    result = subprocess.run(['docker-compose', 'build', '--no-cache', 'frontend'], 
                          capture_output=True, text=True, timeout=300)
    
    if result.returncode == 0:
        print("✅ Frontend container built successfully")
        return True
    else:
        print("❌ Frontend container build failed:")
        print(result.stderr[-500:])  # Last 500 chars of error
        return False

def start_services_step_by_step():
    """Start services in proper order"""
    print("🚀 Starting services step by step...")
    
    services = ['redis', 'backend', 'worker', 'frontend']
    
    for service in services:
        print(f"🔄 Starting {service}...")
        result = subprocess.run(['docker-compose', 'up', '-d', service], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✅ {service} started successfully")
            time.sleep(5)  # Wait a bit for service to stabilize
        else:
            print(f"❌ {service} failed to start:")
            print(result.stderr)
            return False
    
    return True

def check_final_status():
    """Check final status of all services"""
    print("📊 Checking final service status...")
    
    result = subprocess.run(['docker-compose', 'ps'], 
                          capture_output=True, text=True, timeout=30)
    
    print("Current service status:")
    print(result.stdout)
    
    # Check if services are accessible
    test_commands = [
        ('curl -f http://localhost:8000/health', 'Backend health check'),
        ('curl -f http://localhost/api/health', 'API health via nginx'),
        ('curl -f http://localhost/', 'Frontend accessibility')
    ]
    
    for cmd, description in test_commands:
        print(f"🧪 {description}...")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"✅ {description}: SUCCESS")
        else:
            print(f"❌ {description}: FAILED")

def main():
    """Main fix function"""
    print("🚀 FIXING NGINX CONFIGURATION PROPERLY")
    print("=" * 50)
    
    # Step 1: Backup and create proper config
    backup_current_config()
    create_working_nginx_config()
    
    # Step 2: Fix Docker Compose configuration
    fix_docker_compose_ports()
    
    # Step 3: Test nginx config
    config_valid = test_nginx_config()
    if config_valid is False:
        print("❌ Cannot proceed with invalid nginx config")
        return
    
    # Step 4: Rebuild frontend container
    if not rebuild_frontend():
        print("❌ Cannot proceed with frontend build failure")
        return
    
    # Step 5: Start services properly
    if not start_services_step_by_step():
        print("❌ Services failed to start properly")
        return
    
    # Step 6: Check final status
    check_final_status()
    
    print("\n🎉 NGINX FIX COMPLETED!")
    print("Next steps:")
    print("1. Run: python3 comprehensive_docker_diagnostics.py")
    print("2. If all checks pass, run: python3 complete_https_setup.py")

if __name__ == "__main__":
    main() 