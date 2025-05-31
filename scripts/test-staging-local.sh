#!/usr/bin/env bash
set -euo pipefail

# Configuration
COMPOSE_FILE="infra/staging/docker-compose.staging.yml"
ENV_FILE="infra/staging/.env.staging.test"
TEST_DOMAIN="localhost"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

cleanup() {
    log "Cleaning up test environment..."
    docker compose -f "${COMPOSE_FILE}" --env-file="${ENV_FILE}" down --remove-orphans --volumes 2>/dev/null || true
    rm -f "${ENV_FILE}" 2>/dev/null || true
}

# Set up cleanup trap
trap cleanup EXIT

log "🧪 Testing staging deployment locally"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    error "Docker is not installed or not in PATH"
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    error "Docker Compose is not available"
fi

# Create test environment file
log "Creating test environment file..."
cat > "${ENV_FILE}" << 'EOF'
# Test Environment Configuration
GITHUB_REPOSITORY=test/meme-maker
IMAGE_TAG=latest
STAGING_DOMAIN=localhost
ACME_EMAIL=test@example.com
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=admin12345
S3_BUCKET=clips
ENV=staging
LOG_LEVEL=DEBUG
EOF

log "Environment file created: ${ENV_FILE}"

# Check if compose file exists
if [[ ! -f "${COMPOSE_FILE}" ]]; then
    error "Docker Compose file not found: ${COMPOSE_FILE}"
fi

# Build images locally if they don't exist
log "Building local images..."
docker build -t ghcr.io/test/meme-maker/meme-backend:latest -f Dockerfile.backend .
docker build -t ghcr.io/test/meme-maker/meme-worker:latest -f Dockerfile.worker .

# Start services
log "Starting staging services..."
docker compose -f "${COMPOSE_FILE}" --env-file="${ENV_FILE}" up -d

# Wait for services to be healthy
log "Waiting for services to become healthy..."
MAX_WAIT=300  # 5 minutes
WAIT_TIME=0
INTERVAL=10

while [[ ${WAIT_TIME} -lt ${MAX_WAIT} ]]; do
    UNHEALTHY_COUNT=$(docker compose -f "${COMPOSE_FILE}" --env-file="${ENV_FILE}" ps --format "table {{.Service}}\t{{.Status}}" | grep -c "Up (healthy)" || echo "0")
    TOTAL_COUNT=$(docker compose -f "${COMPOSE_FILE}" --env-file="${ENV_FILE}" ps --services | wc -l)
    
    if [[ ${UNHEALTHY_COUNT} -eq ${TOTAL_COUNT} ]]; then
        success "All services are healthy"
        break
    else
        log "Waiting for services... (${UNHEALTHY_COUNT}/${TOTAL_COUNT} healthy, ${WAIT_TIME}s/${MAX_WAIT}s)"
        sleep ${INTERVAL}
        WAIT_TIME=$((WAIT_TIME + INTERVAL))
    fi
done

if [[ ${WAIT_TIME} -ge ${MAX_WAIT} ]]; then
    warn "Not all services became healthy within timeout"
    log "Current service status:"
    docker compose -f "${COMPOSE_FILE}" --env-file="${ENV_FILE}" ps
fi

# Test endpoints
log "Testing application endpoints..."

# Test health endpoint
log "Testing health endpoint..."
if curl -f -s http://localhost/health > /dev/null; then
    success "✅ Health endpoint responding"
else
    error "❌ Health endpoint not responding"
fi

# Test API documentation
log "Testing API documentation..."
if curl -f -s http://localhost/docs > /dev/null; then
    success "✅ API documentation responding"
else
    error "❌ API documentation not responding"
fi

# Test metrics endpoint
log "Testing metrics endpoint..."
if curl -f -s http://localhost/metrics > /dev/null; then
    success "✅ Metrics endpoint responding"
else
    error "❌ Metrics endpoint not responding"
fi

# Test frontend
log "Testing frontend..."
if curl -f -s http://localhost/ | grep -q "<!DOCTYPE html>"; then
    success "✅ Frontend serving HTML"
else
    error "❌ Frontend not serving HTML"
fi

# Test Prometheus
log "Testing Prometheus endpoint..."
if curl -f -s http://localhost/prometheus/ > /dev/null; then
    success "✅ Prometheus endpoint responding"
else
    warn "⚠️  Prometheus endpoint not responding (this is optional)"
fi

# Show service status
log "Final service status:"
docker compose -f "${COMPOSE_FILE}" --env-file="${ENV_FILE}" ps

# Show logs for any failed services
FAILED_SERVICES=$(docker compose -f "${COMPOSE_FILE}" --env-file="${ENV_FILE}" ps --format "table {{.Service}}\t{{.Status}}" | grep -v "Up" | grep -v "SERVICE" | awk '{print $1}' || true)
if [[ -n "${FAILED_SERVICES}" ]]; then
    warn "Failed services detected: ${FAILED_SERVICES}"
    for service in ${FAILED_SERVICES}; do
        log "Logs for ${service}:"
        docker compose -f "${COMPOSE_FILE}" --env-file="${ENV_FILE}" logs --tail=20 "${service}"
    done
fi

# Show disk usage
log "Docker disk usage:"
docker system df

success "🎉 Staging deployment test completed!"
log "Access the application at: http://localhost"
log "Access Prometheus at: http://localhost/prometheus"
log "Access MinIO console at: http://localhost:9001 (admin/admin12345)"

log "To stop the test environment, run:"
echo "  docker compose -f ${COMPOSE_FILE} --env-file=${ENV_FILE} down --remove-orphans --volumes" 