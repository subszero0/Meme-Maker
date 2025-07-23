#!/bin/bash
set -e

echo "🔄 STAGING ROLLBACK SCRIPT"
echo "========================="
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

print_warning "This will stop all services and revert to a minimal working state"
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Rollback cancelled"
    exit 0
fi

# Step 1: Stop all services
print_status "Step 1: Stopping all services..."
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml down --remove-orphans || {
    print_warning "Some services may not have stopped cleanly"
}
print_success "Services stopped"

# Step 2: Clean up resources
print_status "Step 2: Cleaning up resources..."
docker system prune -f || print_warning "Cleanup had some issues (usually safe)"
print_success "Cleanup completed"

# Step 3: Revert cAdvisor to a known working version
print_status "Step 3: Reverting cAdvisor to known working version..."
sed -i 's/gcr.io\/cadvisor\/cadvisor:v0.53.0/gcr.io\/cadvisor\/cadvisor:v0.47.0/g' docker-compose.staging.monitoring.yml
print_success "cAdvisor reverted to v0.47.0"

# Step 4: Start only core services (no monitoring)
print_status "Step 4: Starting core services only..."
docker-compose -f docker-compose.staging.yml --env-file .env.monitoring.staging up -d
print_success "Core services started"

# Step 5: Wait and verify
print_status "Step 5: Waiting for services to stabilize..."
sleep 30

print_status "Checking core service status..."
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    print_success "Backend is responding"
else
    print_error "Backend is not responding"
fi

if curl -f http://localhost:8082/ > /dev/null 2>&1; then
    print_success "Frontend is responding"  
else
    print_error "Frontend is not responding"
fi

echo ""
print_success "Rollback completed!"
echo ""
echo "📊 CORE SERVICES RUNNING:"
echo "  Application: http://13.126.173.223:8082/"
echo "  Backend API: http://13.126.173.223:8001/health"
echo ""
echo "⚠️  MONITORING SERVICES DISABLED"
echo "To re-enable monitoring, fix the issues and run the deployment script again"
echo ""
echo "🔍 TO INVESTIGATE ISSUES:"
echo "  Check logs: docker-compose -f docker-compose.staging.yml logs --tail=50"
echo "  Check status: docker-compose -f docker-compose.staging.yml ps" 