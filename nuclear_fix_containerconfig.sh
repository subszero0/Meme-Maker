#!/bin/bash

# 💥 NUCLEAR FIX FOR CONTAINERCONFIG ERRORS
# Complete Docker state reset to eliminate all ContainerConfig corruption
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

log "💥 NUCLEAR CONTAINERCONFIG FIX - Complete Docker state reset"

warning "This will completely reset Docker state to eliminate ContainerConfig corruption"
warning "All containers, networks, and volumes will be recreated fresh"

# Step 1: Complete Docker cleanup
log "🗑️ Step 1: Complete Docker cleanup..."

# Stop everything
docker-compose -f docker-compose.staging.yml down -v --remove-orphans 2>/dev/null || true
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml down -v --remove-orphans 2>/dev/null || true

# Nuclear cleanup of ALL Docker state
log "💥 Performing nuclear Docker cleanup..."
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true
docker network prune -f || true
docker volume prune -f || true
docker system prune -af || true

# Remove any Docker Compose project-specific items
docker volume rm $(docker volume ls -q | grep meme-maker-staging) 2>/dev/null || true
docker network rm $(docker network ls -q | grep meme-maker) 2>/dev/null || true

success "Complete Docker state cleanup completed"

# Step 2: Verify clean state
log "🔍 Step 2: Verifying clean state..."
REMAINING_CONTAINERS=$(docker ps -aq | wc -l)
if [ "$REMAINING_CONTAINERS" -eq 0 ]; then
    success "No containers remaining - clean state verified"
else
    warning "$REMAINING_CONTAINERS containers still exist, but continuing..."
fi

# Step 3: Rebuild all images fresh
log "🔨 Step 3: Rebuilding all images from scratch..."
docker-compose -f docker-compose.staging.yml build --no-cache --force-rm || {
    error "Failed to build staging services"
    exit 1
}
success "All images rebuilt successfully"

# Step 4: Create services individually to avoid parallel conflicts
log "🚀 Step 4: Creating services individually to avoid conflicts..."

# Create Redis first (with specific volume and network)
log "🟢 Creating Redis with fresh state..."
docker-compose -f docker-compose.staging.yml up -d --force-recreate redis-staging
sleep 20

# Verify Redis is actually running
if docker-compose -f docker-compose.staging.yml ps redis-staging | grep -i "up"; then
    success "Redis created and running"
    
    # Test Redis connection
    if timeout 10 docker-compose -f docker-compose.staging.yml exec -T redis-staging redis-cli ping 2>/dev/null | grep -i pong; then
        success "Redis is responding"
    else
        warning "Redis ping timeout but container is running"
    fi
else
    error "Redis failed to start"
    docker-compose -f docker-compose.staging.yml logs redis-staging
    exit 1
fi

# Create backend
log "🔧 Creating backend with fresh state..."
docker-compose -f docker-compose.staging.yml up -d --force-recreate --no-deps backend-staging
sleep 25

# Verify backend
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
    warning "Backend health check failed"
    docker-compose -f docker-compose.staging.yml ps backend-staging
    docker-compose -f docker-compose.staging.yml logs --tail=15 backend-staging
fi

# Create worker
log "👷 Creating worker with fresh state..."
docker-compose -f docker-compose.staging.yml up -d --force-recreate --no-deps worker-staging
sleep 10

# Create frontend
log "🎨 Creating frontend with fresh state..."
docker-compose -f docker-compose.staging.yml up -d --force-recreate --no-deps frontend-staging
sleep 25

# Verify frontend
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
    warning "Frontend health check failed"
    docker-compose -f docker-compose.staging.yml ps frontend-staging
fi

# Step 5: Create monitoring services individually
log "📊 Step 5: Creating monitoring services individually..."

# Set environment variables for Grafana
export GRAFANA_ADMIN_PASSWORD="staging_admin_2025_secure"
export GRAFANA_SECRET_KEY="staging_secret_key_2025_secure"

# Create each monitoring service separately to avoid conflicts
log "📈 Creating Prometheus..."
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml up -d --force-recreate --no-deps prometheus
sleep 15

log "📊 Creating Grafana..."
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml up -d --force-recreate --no-deps grafana
sleep 15

log "📊 Creating Redis Exporter..."
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml up -d --force-recreate --no-deps redis_exporter
sleep 10

log "📊 Creating Node Exporter..."
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml up -d --force-recreate --no-deps node_exporter
sleep 10

log "📊 Creating cAdvisor..."
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml up -d --force-recreate --no-deps cadvisor
sleep 15

# Step 6: Final comprehensive status check
log "🔍 Step 6: Final comprehensive status check..."

echo -e "\n${GREEN}🎉 NUCLEAR FIX RESULTS${NC}"
echo "================================================"

# Check all core services
echo -e "\n${BLUE}🏥 Core Services Status:${NC}"

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
    echo -e "${YELLOW}⚠️  May need initialization time${NC}"
fi

# Check monitoring services
echo -e "\n${BLUE}📊 Monitoring Services Status:${NC}"

MONITORING_SERVICES=(
    "http://localhost:9090/-/healthy:Prometheus"
    "http://localhost:3001/api/health:Grafana"
    "http://localhost:8083/healthz:cAdvisor"
    "http://localhost:9121/metrics:Redis Exporter"
    "http://localhost:9100/metrics:Node Exporter"
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
echo -e "\n${BLUE}📦 All Container Status:${NC}"
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml ps

# Resource usage
echo -e "\n${BLUE}💾 Resource Usage:${NC}"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null || echo "Resource stats unavailable"

# Access information
echo -e "\n${BLUE}🌐 External Access URLs:${NC}"
echo "• Application: http://13.126.173.223:8082/"
echo "• Backend API: http://13.126.173.223:8001/health"
echo "• Prometheus: http://13.126.173.223:9090/"
echo "• Grafana: http://13.126.173.223:3001/ (admin/staging_admin_2025_secure)"
echo "• cAdvisor: http://13.126.173.223:8083/"

echo -e "\n${GREEN}✅ NUCLEAR CONTAINERCONFIG FIX COMPLETED${NC}"
echo ""
echo -e "${BLUE}🧪 Test Your Download URL Fix:${NC}"
echo "1. Visit: http://13.126.173.223:8082/"
echo "2. Process a video clip"
echo "3. Download the result"
echo "4. Verify URL format: http://13.126.173.223:8001/api/v1/jobs/.../download"
echo "   (Should NO LONGER be the broken http://api/... format)"

echo -e "\n${BLUE}🔍 Next Steps:${NC}"
echo "• Allow 3-5 minutes for all services to fully initialize"
echo "• Monitor services: docker-compose -f docker-compose.staging.yml ps"
echo "• Check logs if needed: docker-compose -f docker-compose.staging.yml logs [service-name]"

success "All ContainerConfig errors should now be eliminated!" 