#!/bin/bash
set -e

echo "🔧 FIXING STAGING DEPLOYMENT ISSUES..."
echo "======================================"

# Function to print colored output
print_status() {
    echo -e "\033[1;34m$1\033[0m"
}

print_success() {
    echo -e "\033[1;32m✅ $1\033[0m"
}

print_error() {
    echo -e "\033[1;31m❌ $1\033[0m"
}

print_warning() {
    echo -e "\033[1;33m⚠️  $1\033[0m"
}

# Check if we're in the right directory
if [ ! -f "docker-compose.staging.yml" ] || [ ! -f "docker-compose.staging.monitoring.yml" ]; then
    print_error "Not in correct directory! Please run from Meme-Maker-Staging root."
    exit 1
fi

print_status "Step 1: Cleaning up conflicting containers..."

# Stop all containers (including orphaned ones) with ALL staging files
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml --env-file .env.monitoring.staging down --remove-orphans || {
    print_warning "Normal compose down failed, trying force cleanup..."
    
    # Force stop and remove conflicting containers
    echo "Stopping and removing conflicting containers..."
    docker stop meme-maker-redis meme-maker-backend meme-maker-worker meme-maker-frontend-staging || true
    docker rm meme-maker-redis meme-maker-backend meme-maker-worker meme-maker-frontend-staging || true
    docker stop meme-maker-prometheus-staging meme-maker-grafana-staging || true
    docker rm meme-maker-prometheus-staging meme-maker-grafana-staging || true
    
    # Clean up any remaining containers
    docker container prune -f
}

print_success "Containers cleaned up"

print_status "Step 2: Checking required files..."

# Verify all required files exist
REQUIRED_FILES=(
    "docker-compose.staging.yml"
    "docker-compose.staging.monitoring.yml" 
    ".env.monitoring.staging"
    "infra/prometheus/prometheus.staging.yml"
    "infra/prometheus/rules/meme_maker.staging.yml"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_success "Found: $file"
    else
        print_error "Missing: $file"
        exit 1
    fi
done

print_status "Step 3: Creating required directories..."

# Ensure all directories exist
mkdir -p storage/clips storage/downloads storage/uploads
mkdir -p infra/prometheus/rules infra/grafana/dashboards
chmod 755 storage/clips storage/downloads storage/uploads

print_success "Directories created"

print_status "Step 4: Starting services with correct configuration..."

# Start services with correct compose files and environment (staging + monitoring)
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml --env-file .env.monitoring.staging up -d

print_success "Services started"

print_status "Step 5: Waiting for services to initialize..."

# Wait for services to be ready
sleep 30

print_status "Step 6: Checking service health..."

# Check container status
echo "Container Status:"
echo "=================="
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml ps

echo ""
echo "Service Health Checks:"
echo "====================="

# Check backend health (staging port 8001)
if curl -f http://localhost:8001/health >/dev/null 2>&1; then
    print_success "Backend healthy (port 8001)"
else
    print_error "Backend not responding (port 8001)"
fi

# Check frontend (staging port 8082)
if curl -f http://localhost:8082/ >/dev/null 2>&1; then
    print_success "Frontend healthy (port 8082)"
else
    print_error "Frontend not responding (port 8082)"
fi

# Check Prometheus
if curl -f http://localhost:9090/-/healthy >/dev/null 2>&1; then
    print_success "Prometheus healthy (port 9090)"
else
    print_error "Prometheus not responding (port 9090)"
fi

# Check Grafana
if curl -f http://localhost:3001/api/health >/dev/null 2>&1; then
    print_success "Grafana healthy (port 3001)"
else
    print_error "Grafana not responding (port 3001)"
fi

# Check Redis
if curl -f http://localhost:9121/metrics >/dev/null 2>&1; then
    print_success "Redis Exporter healthy (port 9121)"
else
    print_error "Redis Exporter not responding (port 9121)"
fi

print_status "Step 7: Checking container logs for errors..."

echo ""
echo "Recent Container Logs:"
echo "====================="
echo "Backend logs (last 10 lines):"
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml logs --tail=10 backend-staging || true
echo ""
echo "Worker logs (last 10 lines):"
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml logs --tail=10 worker-staging || true
echo ""
echo "Prometheus logs (last 5 lines):"
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml logs --tail=5 prometheus || true
echo ""
echo "Grafana logs (last 5 lines):"
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml logs --tail=5 grafana || true

print_status "Step 8: Testing job processing..."

# Test a simple job processing
echo ""
echo "Testing Job Processing:"
echo "======================="
echo "Sending test job to backend..."

TEST_RESPONSE=$(curl -s -X POST http://localhost:8001/api/clips/start \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "start_time": 0, "end_time": 10}' || echo "FAILED")

if [[ "$TEST_RESPONSE" == *"job_id"* ]]; then
    print_success "Test job submitted successfully"
    echo "Response: $TEST_RESPONSE"
else
    print_error "Test job submission failed"
    echo "Response: $TEST_RESPONSE"
fi

echo ""
echo "🎉 STAGING DEPLOYMENT FIX COMPLETED!"
echo "===================================="
echo ""
echo "📊 Monitoring Access URLs:"
echo "  Application: http://13.126.173.223:8082/"
echo "  Prometheus:  http://13.126.173.223:9090/"
echo "  Grafana:     http://13.126.173.223:3001/"
echo "    Username: admin"
echo "    Password: staging_admin_2025_secure"
echo ""
echo "🔍 If monitoring URLs still don't work:"
echo "  1. Check AWS Lightsail firewall allows ports 9090 and 3001"
echo "  2. Run: sudo ufw status"
echo "  3. If needed: sudo ufw allow 9090 && sudo ufw allow 3001"
echo ""
echo "🐛 If jobs still fail at 40%:"
echo "  1. Check worker logs: docker-compose -f docker-compose.yaml -f docker-compose.staging.monitoring.yml logs worker"
echo "  2. Check backend logs: docker-compose -f docker-compose.yaml -f docker-compose.staging.monitoring.yml logs backend"
echo "  3. Monitor job processing: http://13.126.173.223:9090/graph?g0.expr=clip_jobs_queued_total" 