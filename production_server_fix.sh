#!/bin/bash
# Production Server Fix Script
# ===========================
# Run this script ON the production server (13.126.173.223)
# This script diagnoses and fixes the API routing issue

echo "🔍 PRODUCTION SERVER DIAGNOSTIC & FIX"
echo "======================================"

# Step 1: Check current container status
echo ""
echo "📊 STEP 1: Container Status Check"
echo "Current running containers:"
docker ps

echo ""
echo "Docker Compose service status:"
docker-compose ps

# Step 2: Check API routing
echo ""
echo "📊 STEP 2: API Routing Test"
echo "Testing backend health directly:"
curl -s -o /dev/null -w "Backend direct: %{http_code}\n" http://localhost:8000/health

echo "Testing API routing through nginx:"
curl -s -o /dev/null -w "API routing: %{http_code}\n" http://localhost/api/v1/health

# Step 3: Check nginx configuration
echo ""
echo "📊 STEP 3: Nginx Configuration Check"
echo "Checking nginx configuration in frontend container:"
docker exec meme-maker-frontend cat /etc/nginx/nginx.conf | grep -A 10 -B 5 "location /api"

# Step 4: Check container networking
echo ""
echo "📊 STEP 4: Container Networking Check"
echo "Testing inter-container communication:"
docker exec meme-maker-frontend curl -s -o /dev/null -w "Frontend->Backend: %{http_code}\n" http://backend:8000/health

# Step 5: Restart services if needed
echo ""
echo "🔧 STEP 5: Service Restart (if needed)"
echo "Stopping all services..."
docker-compose down

echo "Starting services..."
docker-compose up -d

echo "Waiting for services to be healthy..."
sleep 30

# Step 6: Final verification
echo ""
echo "🧪 STEP 6: Final Verification"
echo "Testing all endpoints:"
curl -s -o /dev/null -w "Frontend: %{http_code}\n" http://localhost/
curl -s -o /dev/null -w "Backend direct: %{http_code}\n" http://localhost:8000/health
curl -s -o /dev/null -w "API routing: %{http_code}\n" http://localhost/api/v1/health

echo ""
echo "🎉 DIAGNOSTIC COMPLETE!"
echo "========================"
echo "If API routing shows 404, nginx configuration needs fixing."
echo "If backend direct shows connection refused, backend container isn't running."
echo "Expected results:"
echo "  Frontend: 200"
echo "  Backend direct: 200" 
echo "  API routing: 200" 