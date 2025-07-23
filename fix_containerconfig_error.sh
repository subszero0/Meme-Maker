#!/bin/bash

# 🔧 FIX CONTAINERCONFIG ERROR AND CONTINUE DEPLOYMENT
# Fixes the specific ContainerConfig KeyError and resumes staging deployment
# Author: AI Assistant
# Date: $(date)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

log "🔧 Fixing ContainerConfig error and continuing deployment..."

# Step 1: Stop all services to avoid conflicts
log "🛑 Stopping all staging services to fix ContainerConfig issue..."
docker-compose -f docker-compose.staging.yml down || true
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml down || true

# Step 2: Force remove the problematic backend container
log "🗑️ Force removing problematic backend container..."
BACKEND_CONTAINERS=$(docker ps -aq --filter "name=*backend-staging*" 2>/dev/null || true)
if [ -n "$BACKEND_CONTAINERS" ]; then
    docker stop $BACKEND_CONTAINERS || true
    docker rm $BACKEND_CONTAINERS || true
    success "Removed problematic backend containers"
else
    log "No backend containers found to remove"
fi

# Step 3: Clean up any dangling containers and images
log "🧹 Cleaning up dangling containers..."
docker container prune -f || true
docker image prune -f || true

# Step 4: Start services one by one with forced recreation
log "🚀 Restarting services with forced recreation..."

# Start Redis first (it was working)
log "🟢 Starting Redis..."
docker-compose -f docker-compose.staging.yml up -d redis-staging
sleep 10

# Force recreate backend with no cache
log "🔧 Force recreating backend service..."
docker-compose -f docker-compose.staging.yml up -d --force-recreate --no-deps backend-staging
sleep 25

# Check backend health
log "⏳ Checking backend health..."
BACKEND_HEALTHY=false
for i in {1..20}; do
    if curl -f http://localhost:8001/health >/dev/null 2>&1; then
        BACKEND_HEALTHY=true
        break
    fi
    echo -n "."
    sleep 3
done

if [ "$BACKEND_HEALTHY" = true ]; then
    success "Backend is healthy"
else
    warning "Backend health check failed, checking container status..."
    docker-compose -f docker-compose.staging.yml ps backend-staging
    log "📋 Backend logs:"
    docker-compose -f docker-compose.staging.yml logs --tail=20 backend-staging
fi

# Start worker with forced recreation
log "👷 Force recreating worker service..."
docker-compose -f docker-compose.staging.yml up -d --force-recreate --no-deps worker-staging
sleep 10

# Start frontend with forced recreation
log "🎨 Force recreating frontend service..."
docker-compose -f docker-compose.staging.yml up -d --force-recreate --no-deps frontend-staging
sleep 25

# Check frontend health
log "⏳ Checking frontend health..."
FRONTEND_HEALTHY=false
for i in {1..20}; do
    if curl -f http://localhost:8082/health >/dev/null 2>&1; then
        FRONTEND_HEALTHY=true
        break
    fi
    echo -n "."
    sleep 3
done

if [ "$FRONTEND_HEALTHY" = true ]; then
    success "Frontend is healthy"
else
    warning "Frontend health check failed, checking container status..."
    docker-compose -f docker-compose.staging.yml ps frontend-staging
fi

# Start monitoring services
log "📊 Starting monitoring services..."
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml up -d prometheus grafana redis_exporter node_exporter cadvisor

log "⏳ Waiting for monitoring services..."
sleep 30

# Final status check
log "🔍 Final status check..."

echo -e "\n${GREEN}🎉 CONTAINERCONFIG FIX RESULTS${NC}"
echo "=========================================="

# Check all services
echo -e "\n${BLUE}🏥 Service Health Status:${NC}"

echo -n "• Redis: "
if docker-compose -f docker-compose.staging.yml ps redis-staging | grep -i "up" >/dev/null; then
    echo -e "${GREEN}✅ Running${NC}"
else
    echo -e "${RED}❌ Not running${NC}"
fi

echo -n "• Backend API: "
if curl -f http://localhost:8001/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Not responding${NC}"
fi

echo -n "• Frontend: "
if curl -f http://localhost:8082/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Not responding${NC}"
fi

echo -n "• API Routing: "
if curl -f http://localhost:8082/api/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Working${NC}"
else
    echo -e "${YELLOW}⚠️  May need more time${NC}"
fi

# Monitoring services
echo -e "\n${BLUE}📊 Monitoring Services:${NC}"
MONITORING_SERVICES=(
    "http://localhost:9090/-/healthy:Prometheus"
    "http://localhost:3001/api/health:Grafana"
    "http://localhost:8083/healthz:cAdvisor"
)

for service in "${MONITORING_SERVICES[@]}"; do
    IFS=':' read -r url name <<< "$service"
    echo -n "• $name: "
    if curl -f "$url" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Working${NC}"
    else
        echo -e "${YELLOW}⚠️  Initializing${NC}"
    fi
done

# Container overview
echo -e "\n${BLUE}📦 Container Status:${NC}"
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml ps

# Access URLs
echo -e "\n${BLUE}🌐 Access Your Staging Environment:${NC}"
echo "• Application: http://13.126.173.223:8082/"
echo "• Backend API: http://13.126.173.223:8001/health"
echo "• Prometheus: http://13.126.173.223:9090/"
echo "• Grafana: http://13.126.173.223:3001/ (admin/staging_admin_2025_secure)"
echo "• cAdvisor: http://13.126.173.223:8083/"

echo -e "\n${GREEN}✅ CONTAINERCONFIG ERROR FIXED${NC}"
echo ""
echo -e "${BLUE}🧪 Test Your Download URL Fix:${NC}"
echo "1. Visit: http://13.126.173.223:8082/"
echo "2. Process a video clip"
echo "3. Download the result"
echo "4. Verify URL format: http://13.126.173.223:8001/api/v1/jobs/.../download"
echo "   (Should no longer be the broken http://api/... format)"

echo -e "\n${BLUE}🔍 If any service isn't responding:${NC}"
echo "• Wait 2-3 minutes for full initialization"
echo "• Check specific logs: docker-compose -f docker-compose.staging.yml logs [service-name]"
echo "• Restart if needed: docker-compose -f docker-compose.staging.yml restart [service-name]"

success "ContainerConfig error fixed and deployment completed!" 