#!/bin/bash
set -e

echo "🔧 VPS Service Debug & Fix Script"
echo "=================================="

# Check current directory
echo "📍 Current directory: $(pwd)"

# Check if we're in the right location
if [ ! -f "docker-compose.yaml" ]; then
    echo "⚠️  Not in Meme-Maker directory, navigating..."
    cd ~/Meme-Maker
    echo "📍 Now in: $(pwd)"
fi

echo ""
echo "🐳 Docker Services Status:"
echo "=========================="
docker compose ps || echo "❌ Docker compose ps failed"

echo ""
echo "🔍 Service Health Checks:"
echo "========================"

# Check if FastAPI is running
echo "🔸 FastAPI Backend (port 8000):"
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ FastAPI is responding"
    FASTAPI_RESPONSE=$(curl -s http://localhost:8000/health)
    echo "   Response: $FASTAPI_RESPONSE"
else
    echo "❌ FastAPI not responding on localhost:8000"
    echo "   Checking if container is running..."
    docker compose logs backend --tail=10 || echo "   No backend logs available"
fi

# Check if frontend is being served
echo "🔸 Frontend (via Caddy):"
if curl -s http://localhost/ > /dev/null; then
    echo "✅ Frontend is being served"
else
    echo "❌ Frontend not being served"
fi

echo ""
echo "🏥 System Status:"
echo "================="

# Check Caddy status
echo "🔸 Caddy Web Server:"
if systemctl is-active caddy >/dev/null 2>&1; then
    echo "✅ Caddy service is running"
    echo "   Status: $(systemctl is-active caddy)"
else
    echo "❌ Caddy service is not running"
    echo "   Status: $(systemctl is-active caddy)"
    echo "   Attempting to restart Caddy..."
    sudo systemctl restart caddy || echo "   Failed to restart Caddy"
    sleep 3
    echo "   New status: $(systemctl is-active caddy)"
fi

# Check Caddy configuration
echo "🔸 Caddy Configuration:"
if [ -f /etc/caddy/Caddyfile ]; then
    echo "✅ Caddyfile exists"
    echo "   Last modified: $(stat -c %y /etc/caddy/Caddyfile)"
    echo "   Size: $(stat -c %s /etc/caddy/Caddyfile) bytes"
else
    echo "❌ Caddyfile not found"
fi

# Check SSL certificates
echo "🔸 SSL Certificates:"
if [ -d /var/lib/caddy/.local/share/caddy/certificates ]; then
    echo "✅ Certificate directory exists"
    CERT_COUNT=$(find /var/lib/caddy/.local/share/caddy/certificates -name "*.crt" 2>/dev/null | wc -l)
    echo "   Certificate files found: $CERT_COUNT"
else
    echo "❌ Certificate directory not found"
fi

echo ""
echo "🔧 Service Recovery Actions:"
echo "============================"

# Restart services if needed
echo "🔸 Restarting Docker services..."
docker compose down || echo "   Docker compose down failed"
sleep 2
docker compose up -d || echo "   Docker compose up failed"

echo "🔸 Waiting for services to start..."
sleep 10

# Check services again
echo "🔸 Post-restart service check:"
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ FastAPI is now responding"
else
    echo "❌ FastAPI still not responding"
    echo "   Backend logs:"
    docker compose logs backend --tail=20 || echo "   No logs available"
fi

# Test SSL certificate generation
echo "🔸 Testing SSL certificate..."
if timeout 30 curl -k https://memeit.pro/health >/dev/null 2>&1; then
    echo "✅ HTTPS connection successful (ignoring cert validity)"
else
    echo "❌ HTTPS connection failed"
    echo "   Forcing Caddy to reload configuration..."
    sudo systemctl reload caddy || echo "   Caddy reload failed"
fi

echo ""
echo "📊 Final Status Summary:"
echo "======================="
echo "Docker Services:"
docker compose ps 2>/dev/null || echo "Docker compose status unavailable"
echo ""
echo "System Services:"
echo "Caddy: $(systemctl is-active caddy 2>/dev/null || echo 'unknown')"
echo ""
echo "Health Endpoints:"
if curl -s http://localhost:8000/health >/dev/null; then
    echo "✅ Backend: http://localhost:8000/health"
else
    echo "❌ Backend: http://localhost:8000/health"
fi
if curl -s http://localhost/ >/dev/null; then
    echo "✅ Frontend: http://localhost/"
else
    echo "❌ Frontend: http://localhost/"
fi

echo ""
echo "🎯 Debug script completed!" 