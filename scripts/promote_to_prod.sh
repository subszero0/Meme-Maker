#!/usr/bin/env bash
set -euo pipefail

# Configuration
DEPLOY_DIR="${HOME}/meme-maker"
COMPOSE_FILE="infra/production/docker-compose.prod.yml"
ENV_FILE="${DEPLOY_DIR}/.env.prod"
BLUE_PORT=8080
GREEN_PORT=8181
GRACE_PERIOD=120  # 2 minutes grace period for old stack

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
    error "Usage: $0 <git-sha-or-tag> [rollback]"
fi

SHA_OR_TAG="$1"
IS_ROLLBACK="${2:-false}"

# Determine current active stack
CURRENT_STACK="blue"
if docker ps --filter "name=meme-prod-green" --format "table {{.Names}}" | grep -q "green"; then
    CURRENT_STACK="green"
fi

NEXT_STACK="green"
NEXT_PORT=$GREEN_PORT
if [[ "$CURRENT_STACK" == "green" ]]; then
    NEXT_STACK="blue"
    NEXT_PORT=$BLUE_PORT
fi

log "🚀 Starting blue-green deployment to production"
log "📋 SHA/Tag: ${SHA_OR_TAG}"
log "🔄 Current stack: ${CURRENT_STACK}"
log "➡️  Next stack: ${NEXT_STACK}"
log "🌐 Next port: ${NEXT_PORT}"

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

# Store deployment info for potential rollback
PREVIOUS_SHA=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
ROLLBACK_INFO="${DEPLOY_DIR}/.rollback_info"
if [[ "$IS_ROLLBACK" != "true" ]]; then
    echo "${PREVIOUS_SHA}|${CURRENT_STACK}" > "$ROLLBACK_INFO"
    log "📝 Rollback info saved: ${PREVIOUS_SHA} on ${CURRENT_STACK}"
fi

# For non-rollback deployments, fetch and checkout
if [[ "$IS_ROLLBACK" != "true" ]]; then
    log "📥 Fetching latest changes from origin..."
    git fetch origin

    # Check if the SHA/tag exists
    if ! git cat-file -e "${SHA_OR_TAG}" 2>/dev/null; then
        error "Git SHA/tag ${SHA_OR_TAG} does not exist in repository"
    fi

    log "🔄 Checking out ${SHA_OR_TAG}..."
    git checkout "${SHA_OR_TAG}"
fi

# Verify checkout
CURRENT_SHA=$(git rev-parse HEAD)
log "✅ Current HEAD: ${CURRENT_SHA}"

# Check if compose file exists
if [[ ! -f "${COMPOSE_FILE}" ]]; then
    error "Docker Compose file not found: ${COMPOSE_FILE}"
fi

# Ensure production environment file exists
if [[ ! -f "${ENV_FILE}" ]]; then
    error "Production environment file not found: ${ENV_FILE}. Please create it first."
fi

# Update IMAGE_TAG in environment file
log "🏷️  Updating IMAGE_TAG to ${SHA_OR_TAG} in environment file..."
if grep -q "^IMAGE_TAG=" "${ENV_FILE}"; then
    sed -i "s/^IMAGE_TAG=.*/IMAGE_TAG=${SHA_OR_TAG}/" "${ENV_FILE}"
else
    echo "IMAGE_TAG=${SHA_OR_TAG}" >> "${ENV_FILE}"
fi

# Update CADDY_HTTP_PORT for blue-green deployment
log "🌐 Configuring ${NEXT_STACK} stack on port ${NEXT_PORT}..."
if grep -q "^CADDY_HTTP_PORT=" "${ENV_FILE}"; then
    sed -i "s/^CADDY_HTTP_PORT=.*/CADDY_HTTP_PORT=${NEXT_PORT}/" "${ENV_FILE}"
else
    echo "CADDY_HTTP_PORT=${NEXT_PORT}" >> "${ENV_FILE}"
fi

# Export environment variables
export $(grep -v '^#' "${ENV_FILE}" | xargs)

log "🐳 Environment configuration:"
echo "  GITHUB_REPOSITORY: ${GITHUB_REPOSITORY:-not-set}"
echo "  IMAGE_TAG: ${IMAGE_TAG:-not-set}"
echo "  PRODUCTION_DOMAIN: ${PRODUCTION_DOMAIN:-app.memeit.pro}"
echo "  CADDY_HTTP_PORT: ${CADDY_HTTP_PORT:-80}"

# Check Docker availability
if ! command -v docker &> /dev/null; then
    error "Docker is not installed or not in PATH"
fi

if ! docker compose version &> /dev/null; then
    error "Docker Compose is not available"
fi

# Create necessary directories
log "📁 Creating necessary directories..."
mkdir -p logs/deployments
mkdir -p /opt/meme-data

# 1. Pull latest images
log "⬇️  Pulling latest images for ${NEXT_STACK} stack..."
docker compose -f "${COMPOSE_FILE}" --env-file="${ENV_FILE}" pull

# 2. Bring up new stack on alternate port
log "🚀 Starting ${NEXT_STACK} stack..."
docker compose -f "${COMPOSE_FILE}" \
  --project-name "memeit-${NEXT_STACK}" \
  --env-file="${ENV_FILE}" \
  up --detach --wait --remove-orphans

# 3. Health check verification for new stack
log "🏥 Performing health check verification for ${NEXT_STACK} stack..."
MAX_HEALTH_WAIT=180  # 3 minutes for production
HEALTH_WAIT=0
INTERVAL=10

while [[ ${HEALTH_WAIT} -lt ${MAX_HEALTH_WAIT} ]]; do
    UNHEALTHY_CONTAINERS=$(docker compose -f "${COMPOSE_FILE}" \
      --project-name "memeit-${NEXT_STACK}" \
      --env-file="${ENV_FILE}" \
      ps --format "table {{.Name}}\t{{.Status}}" | grep -E "(unhealthy|starting)" | awk '{print $1}' || true)
    
    if [[ -z "${UNHEALTHY_CONTAINERS}" ]]; then
        success "✅ All containers in ${NEXT_STACK} stack are healthy"
        break
    else
        log "⏳ Waiting for ${NEXT_STACK} containers to become healthy: ${UNHEALTHY_CONTAINERS} (${HEALTH_WAIT}s/${MAX_HEALTH_WAIT}s)"
        sleep ${INTERVAL}
        HEALTH_WAIT=$((HEALTH_WAIT + INTERVAL))
    fi
done

if [[ ${HEALTH_WAIT} -ge ${MAX_HEALTH_WAIT} ]]; then
    error "❌ Health check failed: Some containers in ${NEXT_STACK} stack are still unhealthy after ${MAX_HEALTH_WAIT} seconds"
fi

# 4. Smoke test the new stack locally
log "🧪 Running smoke tests against ${NEXT_STACK} stack on port ${NEXT_PORT}..."
SMOKE_TEST_RETRIES=6
SMOKE_RETRY=0

while [[ ${SMOKE_RETRY} -lt ${SMOKE_TEST_RETRIES} ]]; do
    if curl -fsSL --max-time 10 "http://localhost:${NEXT_PORT}/health" > /dev/null; then
        success "✅ Health endpoint responding on ${NEXT_STACK} stack"
        break
    else
        SMOKE_RETRY=$((SMOKE_RETRY + 1))
        if [[ ${SMOKE_RETRY} -ge ${SMOKE_TEST_RETRIES} ]]; then
            error "❌ Smoke test failed: Health endpoint not responding after ${SMOKE_TEST_RETRIES} attempts"
        fi
        log "⏳ Retrying smoke test... (${SMOKE_RETRY}/${SMOKE_TEST_RETRIES})"
        sleep 10
    fi
done

# Additional API endpoint test
if curl -fsSL --max-time 10 "http://localhost:${NEXT_PORT}/docs" > /dev/null; then
    success "✅ API docs endpoint responding on ${NEXT_STACK} stack"
else
    warn "⚠️  API docs endpoint not responding, but continuing deployment"
fi

# 5. Switch Caddy upstreams (hot reload)
log "🔄 Switching Caddy configuration to ${NEXT_STACK} stack..."

# Check if Caddy is available for reload
if command -v caddy &> /dev/null; then
    # Create temporary Caddyfile pointing to new stack
    TEMP_CADDYFILE="/tmp/Caddyfile.${NEXT_STACK}"
    
    # Update Caddyfile to point to new port
    sed "s/:8080/:${NEXT_PORT}/g" infra/caddy/Caddyfile.prod > "${TEMP_CADDYFILE}"
    
    # Hot reload Caddy configuration
    if caddy reload --config "${TEMP_CADDYFILE}" --adapter caddyfile; then
        success "✅ Caddy configuration reloaded to point to ${NEXT_STACK} stack"
    else
        warn "⚠️  Caddy reload failed, manual intervention may be required"
    fi
    
    # Clean up temp file
    rm -f "${TEMP_CADDYFILE}"
else
    warn "⚠️  Caddy not available for hot reload, continuing with deployment"
fi

# 6. Final production smoke test
log "🌐 Running final smoke test against production domain..."
PROD_SMOKE_RETRIES=6
PROD_RETRY=0

while [[ ${PROD_RETRY} -lt ${PROD_SMOKE_RETRIES} ]]; do
    if curl -fsSL --max-time 15 "https://${PRODUCTION_DOMAIN:-app.memeit.pro}/health" > /dev/null; then
        success "✅ Production domain health check passed"
        break
    else
        PROD_RETRY=$((PROD_RETRY + 1))
        if [[ ${PROD_RETRY} -ge ${PROD_SMOKE_RETRIES} ]]; then
            error "❌ Production smoke test failed: Domain not responding after ${PROD_SMOKE_RETRIES} attempts"
        fi
        log "⏳ Retrying production smoke test... (${PROD_RETRY}/${PROD_SMOKE_RETRIES})"
        sleep 15
    fi
done

# 7. Grace period before removing old stack
log "⏰ Grace period: waiting ${GRACE_PERIOD} seconds before removing ${CURRENT_STACK} stack..."
sleep ${GRACE_PERIOD}

# 8. Remove old stack
log "🧹 Removing old ${CURRENT_STACK} stack..."
docker compose -f "${COMPOSE_FILE}" \
  --project-name "memeit-${CURRENT_STACK}" \
  --env-file="${ENV_FILE}" \
  down --volumes --remove-orphans || warn "Failed to remove ${CURRENT_STACK} stack"

# 9. Clean up old images
log "🧹 Cleaning up old Docker images..."
docker image prune -f

# 10. Update Caddy port back to standard
log "🔧 Resetting Caddy port configuration..."
if grep -q "^CADDY_HTTP_PORT=" "${ENV_FILE}"; then
    sed -i "s/^CADDY_HTTP_PORT=.*/CADDY_HTTP_PORT=80/" "${ENV_FILE}"
fi

# 11. Display current service status
log "📊 Current service status:"
docker compose -f "${COMPOSE_FILE}" \
  --project-name "memeit-${NEXT_STACK}" \
  --env-file="${ENV_FILE}" \
  ps

# 12. Log deployment completion
DEPLOY_LOG="${DEPLOY_DIR}/logs/deployments/production.log"
mkdir -p "$(dirname "${DEPLOY_LOG}")"
echo "$(date -u +'%Y-%m-%d %H:%M:%S UTC') | ${CURRENT_SHA} | ${SHA_OR_TAG} | ${PREVIOUS_SHA} | ${CURRENT_STACK}->${NEXT_STACK}" >> "${DEPLOY_LOG}"

# 13. Create rollback script
ROLLBACK_SCRIPT="${DEPLOY_DIR}/rollback_prod.sh"
cat > "${ROLLBACK_SCRIPT}" << EOF
#!/usr/bin/env bash
# Auto-generated rollback script for production deployment
# Generated on: $(date -u +'%Y-%m-%d %H:%M:%S UTC')
# Previous SHA: ${PREVIOUS_SHA}
# Previous Stack: ${CURRENT_STACK}

set -euo pipefail

echo "🔄 Executing rollback to ${PREVIOUS_SHA} on ${CURRENT_STACK} stack..."
cd "${DEPLOY_DIR}"
./scripts/promote_to_prod.sh "${PREVIOUS_SHA}" rollback
EOF
chmod +x "${ROLLBACK_SCRIPT}"

success "🎉 Blue-green deployment completed successfully!"
success "📍 Production URL: https://${PRODUCTION_DOMAIN:-app.memeit.pro}"
success "🔄 Active stack: ${NEXT_STACK}"
success "📝 Rollback script: ${ROLLBACK_SCRIPT}"
echo ""
echo "🚨 To rollback this deployment, run:"
echo "   ${ROLLBACK_SCRIPT}"
echo ""
log "📊 Deployment Summary:"
echo "  Previous SHA: ${PREVIOUS_SHA}"
echo "  Current SHA:  ${CURRENT_SHA}"
echo "  Stack switch: ${CURRENT_STACK} → ${NEXT_STACK}"
echo "  Timestamp:    $(date -u +'%Y-%m-%d %H:%M:%S UTC')" 