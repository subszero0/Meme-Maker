#!/bin/bash

# Meme Maker - Local E2E Test Script
# This script runs the same tests as the CI workflow locally
# Usage: ./infra/tests/e2e/run_local_test.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if required tools are available
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    command -v docker >/dev/null 2>&1 || { log_error "Docker is required but not installed."; exit 1; }
    command -v docker-compose >/dev/null 2>&1 || { log_error "Docker Compose is required but not installed."; exit 1; }
    command -v jq >/dev/null 2>&1 || { log_error "jq is required but not installed."; exit 1; }
    command -v curl >/dev/null 2>&1 || { log_error "curl is required but not installed."; exit 1; }
    command -v npm >/dev/null 2>&1 || { log_error "npm is required but not installed."; exit 1; }
    
    log_success "All prerequisites met"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    docker-compose -f docker-compose.yaml down --volumes --remove-orphans >/dev/null 2>&1 || true
    rm -f .env.test
    log_success "Cleanup completed"
}

# Set up environment
setup_environment() {
    log_info "Setting up test environment..."
    
    cat <<EOF > .env.test
DEBUG=true
REDIS_URL=redis://redis:6379/0
REDIS_DB=0
AWS_ACCESS_KEY_ID=admin
AWS_SECRET_ACCESS_KEY=admin12345
AWS_REGION=us-east-1
AWS_ENDPOINT_URL=http://minio:9000
AWS_ALLOW_HTTP=true
S3_BUCKET=clips
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000","http://localhost"]
MAX_CONCURRENT_JOBS=20
JOB_TIMEOUT=300
RATE_LIMIT=off
MAX_CLIP_SECONDS=180
ENV=test
EOF
    
    log_success "Environment configuration created"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    docker-compose -f docker-compose.yaml --env-file .env.test build --parallel
    log_success "All images built successfully"
}

# Start and wait for services
start_services() {
    log_info "Starting core services..."
    docker-compose -f docker-compose.yaml --env-file .env.test up -d redis minio
    
    # Wait for Redis
    log_info "Waiting for Redis..."
    for i in {1..30}; do
        if docker exec meme-maker-redis redis-cli ping 2>/dev/null | grep -q PONG; then
            log_success "Redis healthy"
            break
        fi
        if [ "$i" -eq 30 ]; then
            log_error "Redis failed to start"
            docker logs meme-maker-redis
            return 1
        fi
        sleep 2
    done
    
    # Wait for MinIO
    log_info "Waiting for MinIO..."
    for i in {1..30}; do
        if curl -f -s http://localhost:9003/minio/health/ready >/dev/null 2>&1; then
            log_success "MinIO healthy"
            break
        fi
        if [ "$i" -eq 30 ]; then
            log_error "MinIO failed to start"
            docker logs meme-maker-minio
            return 1
        fi
        sleep 2
    done
    
    # Create S3 bucket
    log_info "Creating S3 bucket..."
    docker exec meme-maker-minio mc alias set myminio http://localhost:9000 admin admin12345 >/dev/null 2>&1
    docker exec meme-maker-minio mc mb myminio/clips --ignore-existing >/dev/null 2>&1
    log_success "S3 bucket ready"
    
    # Start backend and worker
    log_info "Starting backend and worker..."
    docker-compose -f docker-compose.yaml --env-file .env.test up -d backend worker
    
    # Wait for backend
    log_info "Waiting for backend..."
    for i in {1..60}; do
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
        if [ "$STATUS" == "200" ]; then
            HEALTH_RESPONSE=$(curl -s http://localhost:8000/health 2>/dev/null)
            if echo "$HEALTH_RESPONSE" | jq -e '.status == "ok"' >/dev/null 2>&1; then
                log_success "Backend healthy"
                break
            fi
        fi
        if [ "$i" -eq 60 ]; then
            log_error "Backend failed to become healthy"
            return 1
        fi
        sleep 2
    done
}

# Run backend tests
run_backend_tests() {
    log_info "Running backend tests..."
    
    if docker exec meme-maker-backend bash -c "cd /app && python -m pytest -v --tb=short" >/dev/null 2>&1; then
        log_success "Backend tests passed"
    else
        log_warning "Tests failed, attempting recovery..."
        
        docker exec meme-maker-backend bash -c "cd /app && pip install --upgrade -r requirements.txt" >/dev/null 2>&1 || true
        docker-compose -f docker-compose.yaml --env-file .env.test restart backend >/dev/null 2>&1
        
        sleep 10
        if docker exec meme-maker-backend bash -c "cd /app && python -m pytest -v --tb=short" >/dev/null 2>&1; then
            log_success "Backend tests passed after recovery"
        else
            log_error "Backend tests failed after recovery attempt"
            return 1
        fi
    fi
}

# Build and deploy frontend
build_frontend() {
    log_info "Building frontend..."
    
    cd frontend
    npm ci >/dev/null 2>&1
    
    if npm run build >/dev/null 2>&1; then
        log_success "Frontend build successful"
    else
        log_error "Frontend build failed"
        cd ..
        return 1
    fi
    
    if [ ! -f "out/index.html" ]; then
        log_error "Frontend build output missing"
        cd ..
        return 1
    fi
    
    cd ..
    
    # Deploy to backend
    log_info "Deploying frontend static files..."
    docker exec meme-maker-backend mkdir -p /app/static >/dev/null 2>&1
    docker cp frontend/out/. meme-maker-backend:/app/static/ >/dev/null 2>&1
    
    if docker exec meme-maker-backend test -f /app/static/index.html >/dev/null 2>&1; then
        log_success "Frontend files deployed to backend"
    else
        log_error "Frontend deployment failed"
        return 1
    fi
    
    # Test static file serving
    log_info "Testing static file serving..."
    sleep 5
    
    for i in {1..10}; do
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ 2>/dev/null || echo "000")
        if [ "$HTTP_CODE" == "200" ]; then
            log_success "Static files served successfully"
            break
        fi
        if [ "$i" -eq 10 ]; then
            log_error "Static file serving failed (HTTP $HTTP_CODE)"
            return 1
        fi
        sleep 2
    done
}

# Run worker smoke test
run_worker_test() {
    log_info "Running worker smoke test..."
    
    TEST_URL="https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/10s.mp4"
    
    # Enqueue job
    log_info "Enqueuing test job..."
    JOB_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/jobs \
        -H "Content-Type: application/json" \
        -d "{\"url\":\"$TEST_URL\",\"start\":\"00:00:00\",\"end\":\"00:00:05\"}" 2>/dev/null)
    
    JOB_ID=$(echo "$JOB_RESPONSE" | jq -r '.job_id' 2>/dev/null || echo "")
    if [ -z "$JOB_ID" ] || [ "$JOB_ID" == "null" ]; then
        log_error "Failed to enqueue job: $JOB_RESPONSE"
        return 1
    fi
    
    log_success "Job enqueued: $JOB_ID"
    
    # Poll job status
    log_info "Waiting for job completion..."
    for i in {1..40}; do
        sleep 3
        
        JOB_STATUS_RESPONSE=$(curl -s http://localhost:8000/api/v1/jobs/$JOB_ID 2>/dev/null || echo '{"status":"unknown"}')
        STATUS=$(echo "$JOB_STATUS_RESPONSE" | jq -r '.status' 2>/dev/null || echo "unknown")
        
        if [ "$STATUS" == "done" ]; then
            log_success "Job completed successfully"
            break
        elif [ "$STATUS" == "error" ]; then
            log_error "Job failed with error"
            return 1
        elif [ "$i" -eq 40 ]; then
            log_error "Job did not complete within timeout"
            return 1
        fi
        
        if [ $((i % 10)) -eq 0 ]; then
            log_info "Job status: $STATUS (attempt $i/40)"
        fi
    done
    
    # Test download
    log_info "Testing file download..."
    FINAL_STATUS=$(curl -s http://localhost:8000/api/v1/jobs/$JOB_ID 2>/dev/null)
    DOWNLOAD_URL=$(echo "$FINAL_STATUS" | jq -r '.link' 2>/dev/null || echo "")
    
    if [ -z "$DOWNLOAD_URL" ] || [ "$DOWNLOAD_URL" == "null" ]; then
        log_error "No download URL provided"
        return 1
    fi
    
    # First download
    HTTP_CODE=$(curl -s -o /tmp/${JOB_ID}.mp4 -w "%{http_code}" "$DOWNLOAD_URL" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" != "200" ]; then
        log_error "Download failed (HTTP $HTTP_CODE)"
        return 1
    fi
    
    FILE_SIZE=$(stat -c%s "/tmp/${JOB_ID}.mp4" 2>/dev/null || echo "0")
    if [ "$FILE_SIZE" -eq 0 ]; then
        log_error "Downloaded file is empty"
        return 1
    fi
    
    log_success "Download succeeded (${FILE_SIZE} bytes)"
    
    # Test auto-deletion
    log_info "Testing auto-deletion..."
    sleep 2
    HTTP_CODE2=$(curl -s -o /dev/null -w "%{http_code}" "$DOWNLOAD_URL" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE2" == "200" ]; then
        log_error "File still accessible after first download"
        return 1
    fi
    
    log_success "File auto-deleted successfully"
}

# Main execution
main() {
    echo "🧪 Meme Maker Local E2E Test"
    echo "=============================="
    
    # Set up error handling
    trap cleanup EXIT
    
    check_prerequisites
    setup_environment
    build_images
    start_services
    run_backend_tests
    build_frontend
    run_worker_test
    
    log_success "🎉 All tests completed successfully!"
    
    # Manual cleanup since we're successful
    cleanup
    trap - EXIT
}

# Run main function
main "$@" 