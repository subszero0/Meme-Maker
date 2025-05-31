#!/usr/bin/env bash
set -euo pipefail

# Configuration
REGISTRY="ghcr.io"
OWNER=${GITHUB_REPOSITORY_OWNER:-}
REPO_NAME=${GITHUB_REPOSITORY##*/}
IMAGE_TAG=${GITHUB_SHA:-local}
GITHUB_REF_NAME=${GITHUB_REF_NAME:-main}

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

# Validate environment
if [[ -z "${OWNER}" ]]; then
    error "GITHUB_REPOSITORY_OWNER not set"
fi

if [[ -z "${REPO_NAME}" ]]; then
    error "GITHUB_REPOSITORY not set or invalid"
fi

# Image names
BACKEND_IMAGE="${REGISTRY}/${OWNER}/${REPO_NAME}/meme-backend"
WORKER_IMAGE="${REGISTRY}/${OWNER}/${REPO_NAME}/meme-worker"

log "Building and pushing images for repository: ${OWNER}/${REPO_NAME}"
log "Image tag: ${IMAGE_TAG}"
log "Branch: ${GITHUB_REF_NAME}"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    error "Docker is not installed or not in PATH"
fi

# Check if we can connect to Docker daemon
if ! docker info &> /dev/null; then
    error "Cannot connect to Docker daemon"
fi

# Login to GHCR
log "Logging in to GitHub Container Registry..."
if [[ -n "${GHCR_PAT:-}" ]]; then
    echo "${GHCR_PAT}" | docker login ${REGISTRY} -u ${OWNER} --password-stdin
else
    error "GHCR_PAT environment variable not set"
fi

# Build backend image
log "Building backend image..."
docker build \
    --tag "${BACKEND_IMAGE}:${IMAGE_TAG}" \
    --tag "${BACKEND_IMAGE}:latest" \
    --file Dockerfile.backend \
    --platform linux/amd64 \
    --provenance=false \
    .

# Build worker image  
log "Building worker image..."
docker build \
    --tag "${WORKER_IMAGE}:${IMAGE_TAG}" \
    --tag "${WORKER_IMAGE}:latest" \
    --file Dockerfile.worker \
    --platform linux/amd64 \
    --provenance=false \
    .

# Tag with semantic version if on release branch
if [[ "${GITHUB_REF_NAME}" =~ ^release/v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    VERSION=${GITHUB_REF_NAME#release/}
    log "Tagging images with version: ${VERSION}"
    
    docker tag "${BACKEND_IMAGE}:${IMAGE_TAG}" "${BACKEND_IMAGE}:${VERSION}"
    docker tag "${WORKER_IMAGE}:${IMAGE_TAG}" "${WORKER_IMAGE}:${VERSION}"
fi

# Push images
log "Pushing backend image..."
docker push "${BACKEND_IMAGE}:${IMAGE_TAG}"
docker push "${BACKEND_IMAGE}:latest"

log "Pushing worker image..."
docker push "${WORKER_IMAGE}:${IMAGE_TAG}"
docker push "${WORKER_IMAGE}:latest"

# Push version tags if they exist
if [[ "${GITHUB_REF_NAME}" =~ ^release/v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    VERSION=${GITHUB_REF_NAME#release/}
    log "Pushing version tags..."
    docker push "${BACKEND_IMAGE}:${VERSION}"
    docker push "${WORKER_IMAGE}:${VERSION}"
fi

# Output image information
log "Image details:"
echo "  Backend: ${BACKEND_IMAGE}:${IMAGE_TAG}"
echo "  Worker:  ${WORKER_IMAGE}:${IMAGE_TAG}"

if [[ "${GITHUB_REF_NAME}" =~ ^release/v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    VERSION=${GITHUB_REF_NAME#release/}
    echo "  Backend (version): ${BACKEND_IMAGE}:${VERSION}"
    echo "  Worker (version):  ${WORKER_IMAGE}:${VERSION}"
fi

# Clean up local images to save space
log "Cleaning up local images..."
docker image prune -f

success "✅ Images built and pushed successfully!"

# Output for GitHub Actions
if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
    echo "backend-image=${BACKEND_IMAGE}:${IMAGE_TAG}" >> "${GITHUB_OUTPUT}"
    echo "worker-image=${WORKER_IMAGE}:${IMAGE_TAG}" >> "${GITHUB_OUTPUT}"
    echo "image-tag=${IMAGE_TAG}" >> "${GITHUB_OUTPUT}"
fi 