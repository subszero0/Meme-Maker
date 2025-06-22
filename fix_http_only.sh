#!/bin/bash
echo "🔧 Fixing to HTTP-only configuration until SSL certificates are ready..."

cd /home/ubuntu/Meme-Maker

# Stop containers
echo "🛑 Stopping containers..."
docker-compose down

# Replace nginx config with HTTP-only version
echo "📝 Updating nginx configuration to HTTP-only..."
cp nginx_http_only.conf frontend-new/nginx.conf

# Update docker-compose.yaml to remove SSL volumes and port 443
echo "📝 Updating Docker Compose to remove SSL dependencies..."
cat > docker-compose-temp.yaml << 'EOF'
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
      - BASE_URL=http://memeit.pro
      - CORS_ORIGINS=["http://memeit.pro", "http://www.memeit.pro", "http://13.126.173.223"]
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

# Replace the existing docker-compose.yaml
cp docker-compose-temp.yaml docker-compose.yaml
rm docker-compose-temp.yaml

echo "🏗️ Building and starting services with HTTP-only configuration..."
docker-compose up -d --build

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 15

# Check container status
echo "📊 Checking container status..."
docker-compose ps

# Test endpoints
echo "🔍 Testing endpoints..."
echo "Testing localhost health..."
curl -s -o /dev/null -w "Localhost health: %{http_code}\n" http://localhost:8000/health || echo "❌ Localhost health failed"

echo "Testing frontend on port 80..."
curl -s -o /dev/null -w "Frontend port 80: %{http_code}\n" http://localhost:80/ || echo "❌ Frontend port 80 failed"

echo "Testing IP access..."
curl -s -o /dev/null -w "IP access: %{http_code}\n" http://13.126.173.223/ || echo "❌ IP access failed"

echo "Testing domain access..."
curl -s -o /dev/null -w "Domain access: %{http_code}\n" http://memeit.pro/ || echo "❌ Domain access failed"

echo "Testing API through nginx..."
curl -s -o /dev/null -w "API through nginx: %{http_code}\n" http://localhost:80/api/health || echo "❌ API through nginx failed"

echo ""
echo "🎯 HTTP-only configuration applied!"
echo "✅ If all tests show status 200, you can now proceed with SSL setup."
echo "📋 Next step: Run './setup_ssl_certificate.sh' to add HTTPS support." 