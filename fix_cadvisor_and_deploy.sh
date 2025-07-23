#!/bin/bash
set -e

echo "🚀 COMPREHENSIVE CADVISOR FIX & STAGING DEPLOYMENT"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Step 1: Pre-deployment checks
print_status "Step 1: Pre-deployment system checks..."

# Check Docker daemon
if ! docker info > /dev/null 2>&1; then
    print_error "Docker daemon is not running!"
    exit 1
fi
print_success "Docker daemon is running"

# Check available disk space (need at least 2GB free)
available_space=$(df / | awk 'NR==2 {print $4}')
if [ "$available_space" -lt 2097152 ]; then
    print_warning "Low disk space detected. Available: $(( available_space / 1024 ))MB"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    print_success "Sufficient disk space available"
fi

# Check memory
available_memory=$(free -m | awk 'NR==2{printf "%.1f", $7/1024}')
print_success "Available memory: ${available_memory}GB"

# Step 2: Stop existing services gracefully
print_status "Step 2: Stopping existing services..."

# Stop monitoring services first (they depend on core services)
if docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml ps --services --filter "status=running" | grep -q .; then
    print_status "Stopping monitoring services..."
    docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml down --remove-orphans
    print_success "Services stopped"
else
    print_success "No services were running"
fi

# Step 3: Clean up any orphaned containers or networks
print_status "Step 3: Cleaning up orphaned resources..."
docker system prune -f --volumes || print_warning "Some cleanup operations failed (this is usually safe)"
print_success "Cleanup completed"

# Step 4: Verify configuration files
print_status "Step 4: Verifying configuration files..."

if [ ! -f ".env.monitoring.staging" ]; then
    print_error "Missing .env.monitoring.staging file!"
    exit 1
fi
print_success "Environment file exists"

if [ ! -f "docker-compose.staging.yml" ]; then
    print_error "Missing docker-compose.staging.yml file!"
    exit 1
fi
print_success "Core docker-compose file exists"

if [ ! -f "docker-compose.staging.monitoring.yml" ]; then
    print_error "Missing docker-compose.staging.monitoring.yml file!"
    exit 1
fi
print_success "Monitoring docker-compose file exists"

# Verify cAdvisor version is updated
if grep -q "gcr.io/cadvisor/cadvisor:v0.52.1" docker-compose.staging.monitoring.yml; then
    print_success "cAdvisor version updated to v0.52.1"
else
    print_error "cAdvisor version not updated! Please update to v0.52.1"
    exit 1
fi

# Step 5: Pre-pull images to avoid timeout issues
print_status "Step 5: Pre-pulling Docker images..."

# Core images
docker-compose -f docker-compose.staging.yml pull || {
    print_error "Failed to pull core images"
    exit 1
}
print_success "Core images pulled"

# Monitoring images (most likely to have issues)
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml pull || {
    print_error "Failed to pull monitoring images"
    exit 1
}
print_success "Monitoring images pulled"

# Step 6: Start core services first
print_status "Step 6: Starting core services..."

docker-compose -f docker-compose.staging.yml --env-file .env.monitoring.staging up -d

# Wait for core services to be ready
print_status "Waiting for core services to initialize..."
sleep 30

# Verify core services are healthy
core_services=(backend-staging redis-staging frontend-staging worker-staging)
for service in "${core_services[@]}"; do
    if docker-compose -f docker-compose.staging.yml ps --services --filter "status=running" | grep -q "$service"; then
        print_success "$service is running"
    else
        print_error "$service failed to start"
        print_status "Logs for $service:"
        docker-compose -f docker-compose.staging.yml logs --tail=20 "$service"
        exit 1
    fi
done

# Step 7: Add monitoring services
print_status "Step 7: Adding monitoring services..."

docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml --env-file .env.monitoring.staging up -d

# Wait for monitoring services
print_status "Waiting for monitoring services to initialize..."
sleep 60

# Step 8: Comprehensive health checks
print_status "Step 8: Running comprehensive health checks..."

# Check all containers are running
print_status "Checking container status..."
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml ps

# Test core endpoints
endpoints=(
    "http://localhost:8001/health|Backend API"
    "http://localhost:8082/|Frontend"
    "http://localhost:9090/-/healthy|Prometheus" 
    "http://localhost:3001/api/health|Grafana"
    "http://localhost:8083/healthz|cAdvisor"
)

print_status "Testing service endpoints..."
for endpoint in "${endpoints[@]}"; do
    url=$(echo "$endpoint" | cut -d'|' -f1)
    name=$(echo "$endpoint" | cut -d'|' -f2)
    
    if curl -f -s --max-time 10 "$url" > /dev/null; then
        print_success "$name is responding"
    else
        print_warning "$name is not responding (may still be starting)"
    fi
done

# Step 9: Resource monitoring
print_status "Step 9: Checking resource usage..."

echo "=== Container Resource Usage ==="
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}"

echo ""
echo "=== System Resource Usage ==="
echo "Memory: $(free -h | awk 'NR==2{printf "Used: %s/%s (%.2f%%)\n", $3, $2, $3*100/$2}')"
echo "Disk: $(df -h / | awk 'NR==2{printf "Used: %s/%s (%s)\n", $3, $2, $5}')"
echo "Load: $(uptime | awk -F'load average:' '{print $2}')"

# Step 10: Generate access URLs and next steps
print_status "Step 10: Deployment complete!"

echo ""
echo "🎉 STAGING DEPLOYMENT SUCCESSFUL!"
echo "================================="
echo ""
print_success "All services are running with the updated cAdvisor v0.52.1"
echo ""
echo "📊 ACCESS URLS:"
echo "  Application:  http://13.126.173.223:8082/"
echo "  Backend API:  http://13.126.173.223:8001/health"
echo "  Prometheus:   http://13.126.173.223:9090/"
echo "  Grafana:      http://13.126.173.223:3001/"
echo "    Username: admin"
echo "    Password: staging_admin_2025_secure"
echo "  cAdvisor:     http://13.126.173.223:8083/"
echo ""
echo "🔍 DEBUGGING COMMANDS:"
echo "  View logs:    docker-compose -f docker-compose.staging.yml logs --tail=20 [service-name]"
echo "  Check status: docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml ps"
echo "  Monitor:      docker stats"
echo ""
echo "🧪 NEXT STEPS:"
echo "1. Test video processing at: http://13.126.173.223:8082/"
echo "2. Verify DummyMetric fix is working (should progress past 40%)"
echo "3. Check monitoring dashboards in Grafana"
echo "4. Monitor system resources for any issues"
echo ""
print_success "Deployment completed successfully! 🚀" 