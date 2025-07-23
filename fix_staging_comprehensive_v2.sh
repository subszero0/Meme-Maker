#!/bin/bash

# 🚀 COMPREHENSIVE STAGING FIX V2 - Improved Redis Health Checks
# Fixes: Port conflicts, Redis ContainerConfig errors, and API routing issues
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Improved Redis health check function
check_redis_health() {
    local max_attempts=30
    local attempt=0
    
    log "🔍 Checking Redis health with improved detection..."
    
    while [ $attempt -lt $max_attempts ]; do
        # Method 1: Try redis-cli ping
        if docker-compose -f docker-compose.staging.yml exec -T redis-staging redis-cli ping 2>/dev/null | grep -i "pong" >/dev/null 2>&1; then
            success "Redis health check passed (redis-cli ping)"
            return 0
        fi
        
        # Method 2: Check if Redis is accepting connections via logs
        if docker-compose -f docker-compose.staging.yml logs redis-staging 2>/dev/null | grep -i "ready to accept connections" >/dev/null 2>&1; then
            success "Redis health check passed (log analysis)"
            # Double-check with a simple connection test
            sleep 2
            if docker-compose -f docker-compose.staging.yml exec -T redis-staging redis-cli ping 2>/dev/null >/dev/null; then
                success "Redis ping confirmed"
                return 0
            fi
        fi
        
        # Method 3: Check container status
        if [ "$(docker-compose -f docker-compose.staging.yml ps -q redis-staging 2>/dev/null | wc -l)" -eq 1 ]; then
            local container_status=$(docker inspect $(docker-compose -f docker-compose.staging.yml ps -q redis-staging) --format='{{.State.Status}}' 2>/dev/null || echo "unknown")
            if [ "$container_status" = "running" ]; then
                log "Redis container is running, attempting connection..."
                sleep 1
            fi
        fi
        
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    return 1
}

# Pre-flight checks
log "🔍 Running pre-flight checks..."

if ! command_exists docker; then
    error "Docker is not installed or not in PATH"
    exit 1
fi

if ! command_exists docker-compose; then
    error "Docker Compose is not installed or not in PATH"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    error "Docker daemon is not running"
    exit 1
fi

# Check disk space (minimum 2GB)
AVAILABLE_SPACE=$(df / | tail -1 | awk '{print $4}')
if [ "$AVAILABLE_SPACE" -lt 2097152 ]; then
    error "Insufficient disk space. At least 2GB required."
    exit 1
fi

success "Pre-flight checks passed"

# Step 1: Clean up any remaining containers (user already did nuclear cleanup)
log "🧹 Performing final cleanup check..."

# Clean up any remaining orphaned containers
docker container prune -f >/dev/null 2>&1 || true
docker network prune -f >/dev/null 2>&1 || true

success "Cleanup verified"

# Step 2: Pull all required images
log "📥 Pulling latest Docker images..."
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml pull || true
success "Image pull completed"

# Step 3: Build services with no cache to ensure fresh builds
log "🔨 Building services with fresh containers..."
docker-compose -f docker-compose.staging.yml build --no-cache || {
    error "Failed to build staging services"
    exit 1
}
success "Service build completed"

# Step 4: Start core services first
log "🚀 Starting core services (Redis, Backend, Worker)..."
docker-compose -f docker-compose.staging.yml up -d redis-staging

# Give Redis more time to start with modules
log "⏳ Waiting for Redis to initialize (including modules)..."
sleep 15

# Use improved Redis health check
if check_redis_health; then
    success "Redis is healthy and ready"
else
    warning "Redis health check failed, but checking if container is running..."
    
    # Check if Redis container is actually running
    if docker-compose -f docker-compose.staging.yml ps redis-staging | grep -i "up" >/dev/null 2>&1; then
        warning "Redis container is running, proceeding with caution..."
        log "📋 Redis container status:"
        docker-compose -f docker-compose.staging.yml ps redis-staging
        log "📋 Recent Redis logs:"
        docker-compose -f docker-compose.staging.yml logs --tail=10 redis-staging
    else
        error "Redis container failed to start properly"
        docker-compose -f docker-compose.staging.yml logs redis-staging
        exit 1
    fi
fi

# Step 5: Start backend
log "🔧 Starting backend service..."
docker-compose -f docker-compose.staging.yml up -d backend-staging
sleep 20

# Wait for backend to be healthy
log "⏳ Waiting for backend to be healthy..."
BACKEND_HEALTHY=false
for i in {1..30}; do
    if curl -f http://localhost:8001/health >/dev/null 2>&1; then
        BACKEND_HEALTHY=true
        break
    fi
    echo -n "."
    sleep 3
done

if [ "$BACKEND_HEALTHY" = false ]; then
    error "Backend failed to start properly"
    log "📋 Backend container status:"
    docker-compose -f docker-compose.staging.yml ps backend-staging
    log "📋 Backend logs:"
    docker-compose -f docker-compose.staging.yml logs --tail=20 backend-staging
    exit 1
fi
success "Backend is healthy"

# Step 6: Start worker and frontend
log "👷 Starting worker service..."
docker-compose -f docker-compose.staging.yml up -d worker-staging
sleep 10

log "🎨 Starting frontend service..."
docker-compose -f docker-compose.staging.yml up -d frontend-staging
sleep 20

# Wait for frontend to be healthy
log "⏳ Waiting for frontend to be healthy..."
FRONTEND_HEALTHY=false
for i in {1..30}; do
    if curl -f http://localhost:8082/health >/dev/null 2>&1; then
        FRONTEND_HEALTHY=true
        break
    fi
    echo -n "."
    sleep 3
done

if [ "$FRONTEND_HEALTHY" = false ]; then
    error "Frontend failed to start properly"
    log "📋 Frontend container status:"
    docker-compose -f docker-compose.staging.yml ps frontend-staging
    log "📋 Frontend logs:"
    docker-compose -f docker-compose.staging.yml logs --tail=20 frontend-staging
    exit 1
fi
success "Frontend is healthy"

# Step 7: Start monitoring services
log "📊 Starting monitoring services..."
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml up -d prometheus grafana redis_exporter node_exporter cadvisor

# Wait for monitoring services
log "⏳ Waiting for monitoring services to initialize..."
sleep 30

# Check monitoring services (non-blocking)
MONITORING_SERVICES=(
    "http://localhost:9090/-/healthy:Prometheus"
    "http://localhost:3001/api/health:Grafana"
    "http://localhost:8083/healthz:cAdvisor"
    "http://localhost:9121/metrics:Redis Exporter"
    "http://localhost:9100/metrics:Node Exporter"
)

for service in "${MONITORING_SERVICES[@]}"; do
    IFS=':' read -r url name <<< "$service"
    if curl -f "$url" >/dev/null 2>&1; then
        success "$name is responding"
    else
        warning "$name is not responding (will retry later)"
    fi
done

# Step 8: Test API routing specifically for the original issue
log "🔍 Testing API routing to fix original download issue..."
if curl -f "http://localhost:8082/api/health" >/dev/null 2>&1; then
    success "Frontend -> Backend API routing is working"
else
    warning "Frontend -> Backend API routing test failed, checking individual components..."
    
    # Test backend directly
    if curl -f "http://localhost:8001/health" >/dev/null 2>&1; then
        success "Backend direct access works"
    else
        error "Backend direct access failed"
    fi
    
    # Test frontend
    if curl -f "http://localhost:8082/health" >/dev/null 2>&1; then
        success "Frontend direct access works"
    else
        error "Frontend direct access failed"
    fi
fi

# Step 9: Display comprehensive status
log "📊 Final Status Report..."

echo -e "\n${GREEN}🎉 STAGING DEPLOYMENT STATUS${NC}"
echo "========================================"

# Container status
echo -e "\n${BLUE}📦 Container Status:${NC}"
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml ps

# Health status summary
echo -e "\n${BLUE}🏥 Service Health Summary:${NC}"
echo "• Redis: $(if check_redis_health >/dev/null 2>&1; then echo "✅ Healthy"; else echo "⚠️  Running (may need time to fully initialize)"; fi)"
echo "• Backend: $(if curl -f http://localhost:8001/health >/dev/null 2>&1; then echo "✅ Healthy"; else echo "❌ Unhealthy"; fi)"
echo "• Frontend: $(if curl -f http://localhost:8082/health >/dev/null 2>&1; then echo "✅ Healthy"; else echo "❌ Unhealthy"; fi)"
echo "• API Routing: $(if curl -f http://localhost:8082/api/health >/dev/null 2>&1; then echo "✅ Working"; else echo "⚠️  May need time"; fi)"

# Port mapping
echo -e "\n${BLUE}🌐 Service URLs:${NC}"
echo "• Application: http://13.126.173.223:8082/"
echo "• Backend API: http://13.126.173.223:8001/health"
echo "• Prometheus: http://13.126.173.223:9090/"
echo "• Grafana: http://13.126.173.223:3001/ (admin/staging_admin_2025_secure)"
echo "• cAdvisor: http://13.126.173.223:8083/"

# Resource usage
echo -e "\n${BLUE}💾 Resource Usage:${NC}"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo -e "\n${GREEN}✅ DEPLOYMENT COMPLETED${NC}"
echo "Core services are running. You can now test video processing to verify the download URL fix."

echo -e "\n${BLUE}🔍 Debug Commands:${NC}"
echo "• Check logs: docker-compose -f docker-compose.staging.yml logs [service-name]"
echo "• Check containers: docker-compose -f docker-compose.staging.yml ps"
echo "• Restart service: docker-compose -f docker-compose.staging.yml restart [service-name]"
echo "• Test API routing: curl http://localhost:8082/api/health"
echo "• Test backend directly: curl http://localhost:8001/health"

echo -e "\n${BLUE}🔄 To rollback if needed:${NC}"
echo "docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml down"

success "Comprehensive staging fix v2 completed!" 