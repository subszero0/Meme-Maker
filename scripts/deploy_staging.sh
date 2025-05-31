#!/usr/bin/env bash
set -euo pipefail

# Configuration
DEPLOY_DIR="${HOME}/meme-maker"
COMPOSE_FILE="infra/staging/docker-compose.staging.yml"
ENV_FILE="${DEPLOY_DIR}/.env.staging"

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

# Check arguments
if [[ $# -lt 1 ]]; then
    error "Usage: $0 <git-sha> [branch-name]"
fi

GIT_SHA="$1"
BRANCH_NAME="${2:-main}"

log "Starting staging deployment"
log "Git SHA: ${GIT_SHA}"
log "Branch: ${BRANCH_NAME}"
log "Deploy directory: ${DEPLOY_DIR}"

# Validate deploy directory exists
if [[ ! -d "${DEPLOY_DIR}" ]]; then
    error "Deploy directory does not exist: ${DEPLOY_DIR}"
fi

# Change to deploy directory
cd "${DEPLOY_DIR}"

# Check if it's a git repository
if [[ ! -d ".git" ]]; then
    error "Deploy directory is not a git repository"
fi

# Store current deployment info
PREVIOUS_SHA=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
log "Previous deployment SHA: ${PREVIOUS_SHA}"

# Fetch latest changes
log "Fetching latest changes from origin..."
git fetch origin

# Check if the SHA exists
if ! git cat-file -e "${GIT_SHA}" 2>/dev/null; then
    error "Git SHA ${GIT_SHA} does not exist in repository"
fi

# Checkout the specified SHA
log "Checking out ${GIT_SHA}..."
git checkout "${GIT_SHA}"

# Verify checkout
CURRENT_SHA=$(git rev-parse HEAD)
if [[ "${CURRENT_SHA}" != "${GIT_SHA}" ]]; then
    error "Failed to checkout ${GIT_SHA}. Current HEAD is ${CURRENT_SHA}"
fi

# Check if compose file exists
if [[ ! -f "${COMPOSE_FILE}" ]]; then
    error "Docker Compose file not found: ${COMPOSE_FILE}"
fi

# Create staging environment file if it doesn't exist
if [[ ! -f "${ENV_FILE}" ]]; then
    warn "Creating staging environment file: ${ENV_FILE}"
    cat > "${ENV_FILE}" << 'EOF'
# Staging Environment Configuration
GITHUB_REPOSITORY=owner/repo
IMAGE_TAG=latest
STAGING_DOMAIN=staging.memeit.pro
ACME_EMAIL=admin@memeit.pro
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=admin12345
S3_BUCKET=clips
ENV=staging
EOF
fi

# Update IMAGE_TAG in environment file
log "Updating IMAGE_TAG to ${GIT_SHA} in environment file..."
if grep -q "^IMAGE_TAG=" "${ENV_FILE}"; then
    sed -i "s/^IMAGE_TAG=.*/IMAGE_TAG=${GIT_SHA}/" "${ENV_FILE}"
else
    echo "IMAGE_TAG=${GIT_SHA}" >> "${ENV_FILE}"
fi

# Export environment variables
export $(grep -v '^#' "${ENV_FILE}" | xargs)

log "Environment configuration:"
echo "  GITHUB_REPOSITORY: ${GITHUB_REPOSITORY:-not-set}"
echo "  IMAGE_TAG: ${IMAGE_TAG:-not-set}"
echo "  STAGING_DOMAIN: ${STAGING_DOMAIN:-not-set}"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    error "Docker is not installed or not in PATH"
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    error "Docker Compose is not available"
fi

# Pull latest images
log "Pulling latest images..."
docker compose -f "${COMPOSE_FILE}" --env-file="${ENV_FILE}" pull

# Create necessary directories
log "Creating necessary directories..."
mkdir -p logs/caddy

# Stop services gracefully with timeout
log "Stopping existing services..."
if docker compose -f "${COMPOSE_FILE}" --env-file="${ENV_FILE}" ps -q | grep -q .; then
    docker compose -f "${COMPOSE_FILE}" --env-file="${ENV_FILE}" stop --timeout 30
fi

# Start services
log "Starting services..."
docker compose -f "${COMPOSE_FILE}" --env-file="${ENV_FILE}" up --detach --wait --remove-orphans

# Health check loop - fail if any container is unhealthy after 90s
log "Performing health check verification..."
MAX_HEALTH_WAIT=90
HEALTH_WAIT=0
INTERVAL=5

while [[ ${HEALTH_WAIT} -lt ${MAX_HEALTH_WAIT} ]]; do
    # Get unhealthy containers
    UNHEALTHY_CONTAINERS=$(docker compose -f "${COMPOSE_FILE}" --env-file="${ENV_FILE}" ps --format "table {{.Name}}\t{{.Status}}" | grep -E "(unhealthy|starting)" | awk '{print $1}' || true)
    
    if [[ -z "${UNHEALTHY_CONTAINERS}" ]]; then
        success "All containers are healthy"
        break
    else
        log "Waiting for containers to become healthy: ${UNHEALTHY_CONTAINERS} (${HEALTH_WAIT}s/${MAX_HEALTH_WAIT}s)"
        sleep ${INTERVAL}
        HEALTH_WAIT=$((HEALTH_WAIT + INTERVAL))
    fi
done

if [[ ${HEALTH_WAIT} -ge ${MAX_HEALTH_WAIT} ]]; then
    error "Health check failed: Some containers are still unhealthy after ${MAX_HEALTH_WAIT} seconds"
fi

# Wait for services to be healthy
log "Waiting for services to become healthy..."
MAX_WAIT=300  # 5 minutes
WAIT_TIME=0
INTERVAL=10

while [[ ${WAIT_TIME} -lt ${MAX_WAIT} ]]; do
    if docker compose -f "${COMPOSE_FILE}" --env-file="${ENV_FILE}" ps --format "table {{.Service}}\t{{.Status}}" | grep -v "Up (healthy)" | grep -q "Up"; then
        log "Waiting for services to become healthy... (${WAIT_TIME}s/${MAX_WAIT}s)"
        sleep ${INTERVAL}
        WAIT_TIME=$((WAIT_TIME + INTERVAL))
    else
        break
    fi
done

# Check final health status
log "Checking service health..."
UNHEALTHY_SERVICES=$(docker compose -f "${COMPOSE_FILE}" --env-file="${ENV_FILE}" ps --format "table {{.Service}}\t{{.Status}}" | grep -v "Up (healthy)" | grep "Up" | awk '{print $1}' || true)

if [[ -n "${UNHEALTHY_SERVICES}" ]]; then
    warn "Some services are not healthy: ${UNHEALTHY_SERVICES}"
    warn "Deployment completed but some services may not be ready"
else
    success "All services are healthy"
fi

# Clean up old images to save disk space
log "Cleaning up old Docker images..."
docker image prune -f

# Display running services
log "Current service status:"
docker compose -f "${COMPOSE_FILE}" --env-file="${ENV_FILE}" ps

# Test health endpoint
log "Testing health endpoint..."
MAX_HEALTH_WAIT=60
HEALTH_WAIT=0

while [[ ${HEALTH_WAIT} -lt ${MAX_HEALTH_WAIT} ]]; do
    if curl -f -s http://localhost/health > /dev/null 2>&1; then
        success "Health endpoint is responding"
        break
    else
        log "Waiting for health endpoint... (${HEALTH_WAIT}s/${MAX_HEALTH_WAIT}s)"
        sleep 5
        HEALTH_WAIT=$((HEALTH_WAIT + 5))
    fi
done

if [[ ${HEALTH_WAIT} -ge ${MAX_HEALTH_WAIT} ]]; then
    error "Health endpoint is not responding after ${MAX_HEALTH_WAIT} seconds"
fi

# Log deployment info
log "Deployment completed successfully!"
echo "  Previous SHA: ${PREVIOUS_SHA}"
echo "  Current SHA:  ${CURRENT_SHA}"
echo "  Branch:       ${BRANCH_NAME}"
echo "  Timestamp:    $(date -u +'%Y-%m-%d %H:%M:%S UTC')"

# Save deployment record
DEPLOY_LOG="${DEPLOY_DIR}/logs/deployments.log"
mkdir -p "$(dirname "${DEPLOY_LOG}")"
echo "$(date -u +'%Y-%m-%d %H:%M:%S UTC') | ${CURRENT_SHA} | ${BRANCH_NAME} | ${PREVIOUS_SHA}" >> "${DEPLOY_LOG}"

success "🚀 Staging deployment completed successfully!"
success "🌐 Application available at: https://${STAGING_DOMAIN:-staging.memeit.pro}" 