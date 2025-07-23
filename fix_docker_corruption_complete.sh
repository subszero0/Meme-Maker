#!/bin/bash
set -e

echo "🚨 COMPREHENSIVE DOCKER CORRUPTION RECOVERY"
echo "=============================================="
echo ""
echo "This script will fix the ContainerConfig error by:"
echo "1. 🧹 Complete Docker cleanup and corruption removal"
echo "2. 🔄 Docker daemon restart and state reset"
echo "3. 🚀 Fresh deployment with cAdvisor v0.52.1 fix"
echo "4. ✅ Comprehensive verification and testing"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}📋 $1${NC}"
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

print_separator() {
    echo ""
    echo "===========================================" 
    echo ""
}

# Step 1: Verify we have all required scripts
print_status "Step 1: Checking required recovery scripts..."

required_scripts=(
    "fix_docker_corruption.sh"
    "fix_cadvisor_and_deploy.sh"
    "create_staging_env.sh"
)

for script in "${required_scripts[@]}"; do
    if [ -f "$script" ]; then
        print_success "Found: $script"
        chmod +x "$script"
    else
        print_error "Missing required script: $script"
        echo "Please ensure all recovery scripts are present before running"
        exit 1
    fi
done

print_separator

# Step 2: Run comprehensive Docker corruption cleanup
print_status "Step 2: Running comprehensive Docker corruption cleanup..."
print_warning "This will remove ALL Docker containers, images, and corrupted state"

echo "Running fix_docker_corruption.sh..."
./fix_docker_corruption.sh

print_success "Docker corruption cleanup completed"
print_separator

# Step 3: Verify Docker daemon is healthy
print_status "Step 3: Verifying Docker daemon health..."

# Test Docker daemon
if ! docker info > /dev/null 2>&1; then
    print_error "Docker daemon is not responding properly"
    print_status "Attempting Docker daemon restart..."
    sudo systemctl restart docker
    sleep 15
    
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker daemon still not responding. Manual intervention required."
        exit 1
    fi
fi

print_success "Docker daemon is healthy"

# Check Docker version
docker_version=$(docker --version)
print_success "Docker version: $docker_version"

print_separator

# Step 4: Create required environment file
print_status "Step 4: Setting up environment configuration..."

if [ ! -f ".env.monitoring.staging" ]; then
    print_status "Creating .env.monitoring.staging..."
    ./create_staging_env.sh
    print_success "Environment file created"
else
    print_success "Environment file already exists"
fi

print_separator

# Step 5: Run comprehensive deployment with cAdvisor fix
print_status "Step 5: Running comprehensive deployment with cAdvisor v0.52.1..."

echo "Executing fix_cadvisor_and_deploy.sh..."
./fix_cadvisor_and_deploy.sh

print_separator

# Step 6: Additional verification and testing
print_status "Step 6: Running additional verification tests..."

echo "Checking container health status..."
containers=$(docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml ps --format table)
echo "$containers"

echo ""
echo "Testing service endpoints..."

# Test core services
services=(
    "http://localhost:8082/ Application"
    "http://localhost:8001/health Backend"
    "http://localhost:9090/-/healthy Prometheus"
    "http://localhost:3001/api/health Grafana"
    "http://localhost:8083/healthz cAdvisor"
)

failed_services=()

for service in "${services[@]}"; do
    url=$(echo "$service" | cut -d' ' -f1)
    name=$(echo "$service" | cut -d' ' -f2-)
    
    if curl -f -s --max-time 10 "$url" > /dev/null 2>&1; then
        print_success "$name: HEALTHY"
    else
        print_warning "$name: NOT RESPONDING"
        failed_services+=("$name")
    fi
done

print_separator

# Step 7: Final status report
print_status "Step 7: Final recovery status report..."

if [ ${#failed_services[@]} -eq 0 ]; then
    print_success "🎉 COMPLETE RECOVERY SUCCESSFUL!"
    echo ""
    echo "✅ All Docker corruption issues resolved"
    echo "✅ cAdvisor v0.52.1 deployed successfully"
    echo "✅ All 5 services are healthy and responding"
    echo ""
    echo "🌐 Access URLs:"
    echo "  Application:  http://13.126.173.223:8082/"
    echo "  Backend API:  http://13.126.173.223:8001/health"
    echo "  Prometheus:   http://13.126.173.223:9090/"
    echo "  Grafana:      http://13.126.173.223:3001/"
    echo "  cAdvisor:     http://13.126.173.223:8083/"
else
    print_warning "Recovery completed with some issues"
    echo ""
    echo "Services that need attention:"
    for service in "${failed_services[@]}"; do
        echo "  - $service"
    done
    echo ""
    echo "Check logs for these services:"
    echo "  docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml logs [service-name]"
fi

echo ""
echo "🔍 Monitoring commands:"
echo "  Status: docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml ps"
echo "  Logs:   docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml logs --tail=20 [service]"
echo "  Stats:  docker stats"

print_separator
print_success "Docker corruption recovery process completed! 🚀" 