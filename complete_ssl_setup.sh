#!/bin/bash
echo "🔒 Completing SSL setup for HTTPS..."

cd /home/ubuntu/Meme-Maker

# Create SSL directories and copy certificates (if not already done)
echo "📁 Setting up SSL certificate directories..."
sudo mkdir -p ssl/certs ssl/private

# Copy certificates from Let's Encrypt to project directory
echo "📄 Copying SSL certificates to project..."
sudo cp /etc/letsencrypt/live/memeit.pro/fullchain.pem ssl/certs/memeit.pro.crt
sudo cp /etc/letsencrypt/live/memeit.pro/privkey.pem ssl/private/memeit.pro.key

# Set correct ownership
sudo chown -R $USER:$USER ssl/

# Verify certificates exist
echo "🔍 Verifying SSL certificates..."
if [ -f "ssl/certs/memeit.pro.crt" ] && [ -f "ssl/private/memeit.pro.key" ]; then
    echo "✅ SSL certificates found and copied successfully"
    ls -la ssl/certs/ ssl/private/
else
    echo "❌ SSL certificates not found. Please check Let's Encrypt setup."
    exit 1
fi

# Update nginx configuration to include HTTPS
echo "📝 Updating nginx configuration for HTTPS..."
cat > frontend-new/nginx.conf << 'EOF'
# PID file in writable location
pid /tmp/nginx.pid;

worker_processes auto;
error_log /var/log/nginx/error.log warn;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging format
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

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

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # HTTP server - redirect to HTTPS for domain
    server {
        listen 80;
        server_name memeit.pro www.memeit.pro;
        
        # Redirect all HTTP traffic to HTTPS
        return 301 https://$server_name$request_uri;
    }

    # HTTP server for IP access (development/testing)
    server {
        listen 80 default_server;
        server_name localhost _;
        root /usr/share/nginx/html;
        index index.html;

        # Security
        server_tokens off;

        # Handle SPA routing
        location / {
            try_files $uri $uri/ /index.html;
            
            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
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
            
            # Mobile-friendly settings
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # WebSocket support for development
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
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }

        # Error pages
        error_page 404 /index.html;
        error_page 500 502 503 504 /50x.html;
        location = /50x.html {
            root /usr/share/nginx/html;
        }
    }

    # HTTPS server for domain
    server {
        listen 443 ssl http2;
        server_name memeit.pro www.memeit.pro;
        root /usr/share/nginx/html;
        index index.html;

        # Security
        server_tokens off;

        # SSL Configuration
        ssl_certificate /etc/ssl/certs/memeit.pro.crt;
        ssl_certificate_key /etc/ssl/private/memeit.pro.key;
        
        # Modern SSL Configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Security headers for HTTPS
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

        # Handle SPA routing
        location / {
            try_files $uri $uri/ /index.html;
            
            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
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
            proxy_set_header X-Forwarded-Proto https;
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
            proxy_set_header X-Forwarded-Proto https;
        }

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }

        # Error pages
        error_page 404 /index.html;
        error_page 500 502 503 504 /50x.html;
        location = /50x.html {
            root /usr/share/nginx/html;
        }
    }
}
EOF

# Update docker-compose.yaml to add HTTPS support
echo "📝 Updating Docker Compose for HTTPS..."
cat > docker-compose.yaml << 'EOF'
version: '3.9'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: meme-maker-backend
    restart: unless-stopped
    environment:
      - DEBUG=false
      - ENVIRONMENT=production
      - REDIS_URL=redis://redis:6379
      - CLIPS_DIR=/app/clips
      - BASE_URL=https://memeit.pro
      - CORS_ORIGINS=["https://memeit.pro", "https://www.memeit.pro", "http://memeit.pro", "http://13.126.173.223"]
    ports:
      - "8000:8000"
    volumes:
      - /opt/meme-maker/storage:/app/clips
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    build:
      context: ./frontend-new
      dockerfile: Dockerfile
    container_name: meme-maker-frontend
    restart: unless-stopped
    environment:
      - NODE_ENV=production
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./ssl/certs:/etc/ssl/certs:ro
      - ./ssl/private:/etc/ssl/private:ro
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:80/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    container_name: meme-maker-worker
    restart: unless-stopped
    environment:
      - REDIS_URL=redis://redis:6379
      - CLIPS_DIR=/app/clips
    volumes:
      - /opt/meme-maker/storage:/app/clips
    depends_on:
      backend:
        condition: service_healthy
      redis:
        condition: service_healthy

  redis:
    image: redis:7.2.5-alpine
    container_name: meme-maker-redis
    restart: always
    command: ["redis-server"]
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 30s

  prometheus:
    image: prom/prometheus
    container_name: meme-maker-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - prometheus-data:/prometheus
      - ./infra/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    container_name: meme-maker-grafana
    restart: unless-stopped
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    ports:
      - "3001:3000"
    volumes:
      - grafana-data:/var/lib/grafana

volumes:
  prometheus-data:
  grafana-data:
EOF

echo "🏗️ Building and starting services with HTTPS support..."
docker-compose up -d --build

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 20

# Check container status
echo "📊 Checking container status..."
docker-compose ps

# Test endpoints
echo "🔍 Testing endpoints..."
echo "Testing localhost health..."
curl -s -o /dev/null -w "Localhost health: %{http_code}\n" http://localhost:8000/health || echo "❌ Localhost health failed"

echo "Testing HTTP (should redirect)..."
curl -s -o /dev/null -w "HTTP redirect: %{http_code}\n" http://memeit.pro/ || echo "❌ HTTP redirect failed"

echo "Testing HTTPS..."
curl -s -o /dev/null -w "HTTPS: %{http_code}\n" https://memeit.pro/ || echo "❌ HTTPS failed"

echo "Testing IP access..."
curl -s -o /dev/null -w "IP access: %{http_code}\n" http://13.126.173.223/ || echo "❌ IP access failed"

echo ""
echo "🎉 SSL setup complete!"
echo "✅ Your application should now be accessible at:"
echo "   🔒 https://memeit.pro (primary HTTPS)"
echo "   🔄 http://memeit.pro (redirects to HTTPS)"
echo "   🔗 http://13.126.173.223 (IP access)"
echo ""
echo "🔍 Check the results above - all should show status 200 or 301 (redirect)." 