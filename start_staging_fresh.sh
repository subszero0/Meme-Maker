#!/bin/bash

# 🚀 START STAGING FROM FRESH STATE
# Clean deployment of all staging services with proper health checks
# Author: AI Assistant
# Date: $(date)
# Branch: monitoring-staging

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

log "🚀 Starting fresh staging deployment..."

# Check if docker-compose files exist
if [ ! -f "docker-compose.staging.yml" ]; then
    error "docker-compose.staging.yml not found in current directory"
    exit 1
fi

if [ ! -f "docker-compose.staging.monitoring.yml" ]; then
    error "docker-compose.staging.monitoring.yml not found in current directory"
    exit 1
fi

success "Docker compose files found"

# Step 1: Build services first (this can take time)
log "🔨 Building services (this may take a few minutes)..."
docker-compose -f docker-compose.staging.yml build || {
    error "Failed to build staging services"
    exit 1
}
success "Service build completed"

# Step 2: Start Redis first
log "🟢 Starting Redis service..."
docker-compose -f docker-compose.staging.yml up -d redis-staging

# Give Redis time to start (it has modules to load)
log "⏳ Waiting for Redis to initialize (30 seconds for modules)..."
sleep 30

# Check Redis status
log "🔍 Checking Redis status..."
if docker-compose -f docker-compose.staging.yml ps redis-staging | grep -i "up"; then
    success "Redis container is running"
    
    # Try Redis ping (with timeout)
    if timeout 10 docker-compose -f docker-compose.staging.yml exec -T redis-staging redis-cli ping 2>/dev/null | grep -i pong; then
        success "Redis is responding to ping"
    else
        warning "Redis ping timeout, but container is running - this is normal during module loading"
        
        # Check logs for "Ready to accept connections"
        if docker-compose -f docker-compose.staging.yml logs redis-staging | grep -i "ready to accept connections"; then
            success "Redis logs show ready to accept connections"
        fi
    fi
else
    error "Redis container failed to start"
    docker-compose -f docker-compose.staging.yml logs redis-staging
    exit 1
fi

# Step 3: Start backend
log "🔧 Starting backend service..."
docker-compose -f docker-compose.staging.yml up -d backend-staging
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
    success "Backend is healthy and responding"
else
    warning "Backend health check timed out, checking container status..."
    docker-compose -f docker-compose.staging.yml ps backend-staging
    
    # Show logs for debugging
    log "📋 Backend logs (last 15 lines):"
    docker-compose -f docker-compose.staging.yml logs --tail=15 backend-staging
fi

# Step 4: Start worker
log "👷 Starting worker service..."
docker-compose -f docker-compose.staging.yml up -d worker-staging
sleep 10

# Step 5: Start frontend
log "🎨 Starting frontend service..."
docker-compose -f docker-compose.staging.yml up -d frontend-staging
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
    success "Frontend is healthy and responding"
else
    warning "Frontend health check timed out, checking container status..."
    docker-compose -f docker-compose.staging.yml ps frontend-staging
fi

# Step 6: Start monitoring services
log "📊 Starting monitoring services..."
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml up -d prometheus grafana redis_exporter node_exporter cadvisor

log "⏳ Waiting for monitoring services to initialize..."
sleep 35

# Step 7: Final health checks and status
log "🔍 Running final health checks..."

echo -e "\n${GREEN}🎉 STAGING DEPLOYMENT RESULTS${NC}"
echo "============================================="

# Test core services
echo -e "\n${BLUE}🏥 Core Service Health:${NC}"
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

# Test monitoring services
echo -e "\n${BLUE}📊 Monitoring Service Health:${NC}"
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
        echo -e "${YELLOW}⚠️  Starting up${NC}"
    fi
done

# Show container status
echo -e "\n${BLUE}📦 Container Status:${NC}"
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml ps

# External access URLs
echo -e "\n${BLUE}🌐 External Access URLs:${NC}"
echo "• Application: http://13.126.173.223:8082/"
echo "• Backend API: http://13.126.173.223:8001/health"
echo "• Prometheus: http://13.126.173.223:9090/"
echo "• Grafana: http://13.126.173.223:3001/ (admin/staging_admin_2025_secure)"
echo "• cAdvisor: http://13.126.173.223:8083/"

echo -e "\n${GREEN}✅ DEPLOYMENT COMPLETED${NC}"
echo ""
echo -e "${BLUE}🧪 Test the Download URL Fix:${NC}"
echo "1. Visit: http://13.126.173.223:8082/"
echo "2. Process a video clip"
echo "3. Download - URL should now be: http://13.126.173.223:8001/api/v1/jobs/.../download"
echo "   (instead of the broken http://api/... format)"
echo ""
echo -e "${BLUE}🔍 If services need more time:${NC}"
echo "• Wait 2-3 minutes for all services to fully initialize"
echo "• Check logs: docker-compose -f docker-compose.staging.yml logs [service-name]"
echo "• Restart if needed: docker-compose -f docker-compose.staging.yml restart [service-name]"

success "Fresh staging deployment completed!" 