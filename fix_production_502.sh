#!/bin/bash
# Production 502 Backend Fix Script
# =================================
# This script fixes the 502 Bad Gateway error by ensuring the backend container
# is running and accessible to nginx reverse proxy.
#
# To be run ON the production server via CI/CD deployment

set -e

echo "🚨 FIXING PRODUCTION 502 BACKEND ERROR"
echo "======================================"
echo "Time: $(date)"
echo "Server: $(hostname)"
echo ""

# Navigate to project directory
cd /home/ubuntu/Meme-Maker || {
    echo "❌ Cannot find /home/ubuntu/Meme-Maker directory"
    exit 1
}

echo "📁 Current directory: $(pwd)"
echo "🌿 Current branch: $(git branch --show-current)"
echo ""

# Step 1: Check current container status
echo "📊 STEP 1: Current Container Status"
echo "===================================="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || echo "❌ Docker not available"
echo ""

# Step 2: Check backend container specifically
echo "📊 STEP 2: Backend Container Diagnosis"
echo "======================================"
if docker ps | grep -q "meme-maker-backend"; then
    echo "✅ Backend container is running"
    docker inspect meme-maker-backend --format='{{.State.Health.Status}}' 2>/dev/null || echo "⚠️ No health check available"
else
    echo "❌ Backend container is NOT running"
fi
echo ""

# Step 3: Test backend accessibility
echo "📊 STEP 3: Backend Accessibility Test"
echo "====================================="
echo "Testing backend on localhost:8000..."
if curl -f -s --max-time 5 http://localhost:8000/health > /dev/null; then
    echo "✅ Backend responds on localhost:8000"
else
    echo "❌ Backend NOT responding on localhost:8000"
fi
echo ""

# Step 4: Check docker-compose service status
echo "📊 STEP 4: Docker Compose Service Status"  
echo "========================================"
docker-compose ps 2>/dev/null || echo "⚠️ docker-compose not found or no services"
echo ""

# Step 5: Check recent logs for backend issues
echo "📊 STEP 5: Recent Backend Logs"
echo "=============================="
if docker ps | grep -q "meme-maker-backend"; then
    echo "Last 10 lines of backend logs:"
    docker-compose logs backend --tail=10 2>/dev/null || echo "Cannot get logs"
else
    echo "Backend container not running - no logs available"
fi
echo ""

# Step 6: Apply fix based on container status
echo "🔧 STEP 6: Applying Fix"
echo "======================"

if docker ps | grep -q "meme-maker-backend"; then
    echo "Backend container running but not accessible - restarting backend..."
    docker-compose restart backend
    echo "✅ Backend container restarted"
else
    echo "Backend container not running - starting all services..."
    docker-compose down || echo "No services to stop"
    docker-compose up -d
    echo "✅ All services started"
fi
echo ""

# Step 7: Wait for backend to be ready
echo "⏳ STEP 7: Waiting for Backend to be Ready"
echo "=========================================="
echo "Waiting 30 seconds for backend startup..."
sleep 30

# Progressive health check with retries
for i in {1..6}; do
    echo "Health check attempt $i/6..."
    if curl -f -s --max-time 10 http://localhost:8000/health > /dev/null; then
        echo "✅ Backend health check PASSED!"
        backend_healthy=true
        break
    else
        echo "⏳ Backend not ready yet..."
        sleep 10
    fi
done

if [ "$backend_healthy" != "true" ]; then
    echo "❌ Backend health check FAILED after all retries"
    echo "Checking logs for errors..."
    docker-compose logs backend --tail=20
    exit 1
fi
echo ""

# Step 8: Test API endpoint through nginx
echo "🧪 STEP 8: Testing API Through Nginx"
echo "===================================="
echo "Testing nginx reverse proxy to backend..."
if curl -f -s --max-time 10 http://localhost/api/v1/health > /dev/null; then
    echo "✅ API accessible through nginx reverse proxy"
else
    echo "⚠️ API not accessible through nginx - checking nginx config..."
    
    # Check nginx status
    if sudo systemctl is-active --quiet nginx; then
        echo "✅ Nginx service is running"
        echo "Checking nginx configuration..."
        sudo nginx -t || echo "❌ Nginx configuration error"
    else
        echo "❌ Nginx service is not running"
        echo "Starting nginx..."
        sudo systemctl start nginx
    fi
fi
echo ""

# Step 9: Final production test
echo "🌍 STEP 9: Final Production Test" 
echo "================================"
echo "Testing actual production domain..."

# Test frontend
if curl -f -s --max-time 10 https://memeit.pro > /dev/null; then
    echo "✅ Frontend (https://memeit.pro): Working"
else
    echo "❌ Frontend (https://memeit.pro): Not working"
fi

# Test backend API
if curl -f -s --max-time 10 https://memeit.pro/api/v1/health > /dev/null; then
    echo "✅ Backend API (https://memeit.pro/api/v1/health): Working"
else
    echo "❌ Backend API (https://memeit.pro/api/v1/health): Still failing"
    echo "502 error likely persists - may need manual investigation"
fi
echo ""

# Step 10: Final status summary
echo "📋 STEP 10: Final Status Summary"
echo "================================"
echo "Container status:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep meme-maker || echo "No meme-maker containers running"

echo ""
echo "🎯 FIX COMPLETE!"
echo "==============="
if [ "$backend_healthy" = "true" ]; then
    echo "✅ Backend container is healthy and accessible"
    echo "✅ Fix applied successfully"
    echo "🌍 Test your site: https://memeit.pro"
else
    echo "❌ Backend container issues persist"
    echo "🔍 Manual investigation required on production server"
fi

echo ""
echo "📝 If issues persist, check:"
echo "  1. docker-compose logs backend"
echo "  2. sudo tail -50 /var/log/nginx/error.log"
echo "  3. sudo netstat -tlnp | grep :8000" 