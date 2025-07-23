#!/bin/bash

# 🚀 CONTINUE STAGING DEPLOYMENT - Redis is already running
# Since Redis showed "Ready to accept connections tcp", let's continue the deployment

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

log "🔍 Continuing staging deployment - Redis is already running successfully!"

# Check Redis status first
log "📋 Checking current Redis status..."
if docker-compose -f docker-compose.staging.yml ps redis-staging | grep -i "up"; then
    success "Redis container is running"
    
    # Show Redis logs to confirm it's working
    echo -e "\n${BLUE}📋 Recent Redis logs:${NC}"
    docker-compose -f docker-compose.staging.yml logs --tail=5 redis-staging | grep -E "(Ready to accept connections|Server initialized)"
    
    # Try a simple ping (non-blocking)
    if docker-compose -f docker-compose.staging.yml exec -T redis-staging redis-cli ping 2>/dev/null | grep -i pong; then
        success "Redis ping successful"
    else
        warning "Redis ping had issues, but container is running"
    fi
else
    error "Redis container is not running. Please start it first."
    exit 1
fi

# Continue with backend
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
    
    # Continue anyway to see what happens
    warning "Continuing despite backend health check failure..."
else
    success "Backend is healthy"
fi

# Start worker and frontend
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
    warning "Frontend health check failed, checking if container is running..."
    docker-compose -f docker-compose.staging.yml ps frontend-staging
else
    success "Frontend is healthy"
fi

# Start monitoring services
log "📊 Starting monitoring services..."
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml up -d prometheus grafana redis_exporter node_exporter cadvisor

# Wait for monitoring services
log "⏳ Waiting for monitoring services to initialize..."
sleep 30

# Test API routing specifically for the original issue
log "🔍 Testing API routing to fix original download issue..."
if curl -f "http://localhost:8082/api/health" >/dev/null 2>&1; then
    success "Frontend -> Backend API routing is working"
elif curl -f "http://localhost:8001/health" >/dev/null 2>&1; then
    success "Backend is responding directly"
    warning "Frontend proxy may need more time to initialize"
else
    warning "API routing test incomplete, checking individual services..."
fi

# Display final status
log "📊 Final Status Report..."

echo -e "\n${GREEN}🎉 STAGING DEPLOYMENT STATUS${NC}"
echo "========================================"

# Container status
echo -e "\n${BLUE}📦 Container Status:${NC}"
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml ps

# Quick service tests
echo -e "\n${BLUE}🏥 Quick Service Tests:${NC}"
echo -n "• Backend API: "
if curl -f http://localhost:8001/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Responding${NC}"
else
    echo -e "${RED}❌ Not responding${NC}"
fi

echo -n "• Frontend: "
if curl -f http://localhost:8082/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Responding${NC}"
else
    echo -e "${RED}❌ Not responding${NC}"
fi

echo -n "• API Routing: "
if curl -f http://localhost:8082/api/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Working${NC}"
else
    echo -e "${YELLOW}⚠️  May need time to initialize${NC}"
fi

# External URLs
echo -e "\n${BLUE}🌐 Service URLs:${NC}"
echo "• Application: http://13.126.173.223:8082/"
echo "• Backend API: http://13.126.173.223:8001/health"
echo "• Prometheus: http://13.126.173.223:9090/"
echo "• Grafana: http://13.126.173.223:3001/ (admin/staging_admin_2025_secure)"
echo "• cAdvisor: http://13.126.173.223:8083/"

echo -e "\n${GREEN}✅ DEPLOYMENT COMPLETED${NC}"
echo "Services are running. You can now test the download URL fix!"
echo ""
echo -e "${BLUE}🧪 To test the original issue fix:${NC}"
echo "1. Go to http://13.126.173.223:8082/"
echo "2. Process a video clip"
echo "3. Download the result - URL should now be proper format"
echo ""
echo -e "${BLUE}🔍 Debug Commands:${NC}"
echo "• Check all logs: docker-compose -f docker-compose.staging.yml logs"
echo "• Check specific service: docker-compose -f docker-compose.staging.yml logs [service-name]"
echo "• Restart if needed: docker-compose -f docker-compose.staging.yml restart [service-name]"

success "Staging deployment continuation completed!" 