#!/usr/bin/env bash
# Meme Maker Quick Start Script for macOS/Linux
# This script will set up and start the Meme Maker application

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Flags
SKIP_PREREQS=false
PRODUCTION_MODE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-prereqs)
            SKIP_PREREQS=true
            shift
            ;;
        --production)
            PRODUCTION_MODE=true
            shift
            ;;
        -h|--help)
            echo "Meme Maker Quick Start Script"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-prereqs    Skip prerequisite checks"
            echo "  --production      Start in production mode"
            echo "  -h, --help        Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')]${NC} $1"
}

info() {
    echo -e "${CYAN}$1${NC}"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

check_docker_running() {
    if docker info &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Header
info "🚀 Meme Maker Quick Start"
info "========================="
echo ""

# Check prerequisites
if [[ "$SKIP_PREREQS" != "true" ]]; then
    log "🔍 Checking prerequisites..."
    
    # Check Git
    if ! check_command git; then
        error "❌ Git is not installed or not in PATH"
        warn "Please install Git:"
        warn "  macOS: brew install git"
        warn "  Ubuntu/Debian: sudo apt install git"
        warn "  Or download from: https://git-scm.com/"
        exit 1
    else
        success "✅ Git is installed"
    fi
    
    # Check Docker
    if ! check_command docker; then
        error "❌ Docker is not installed or not in PATH"
        warn "Please install Docker:"
        warn "  macOS: Download Docker Desktop from https://www.docker.com/products/docker-desktop"
        warn "  Linux: sudo apt install docker.io docker-compose"
        exit 1
    else
        success "✅ Docker is installed"
    fi
    
    # Check Docker Compose
    if ! check_command docker-compose && ! docker compose version &> /dev/null; then
        error "❌ Docker Compose is not available"
        warn "Please install Docker Compose:"
        warn "  Usually comes with Docker Desktop"
        warn "  Linux: sudo apt install docker-compose"
        exit 1
    else
        success "✅ Docker Compose is available"
    fi
    
    # Check if Docker is running
    if ! check_docker_running; then
        error "❌ Docker is not running"
        warn "Please start Docker:"
        warn "  macOS: Open Docker Desktop application"
        warn "  Linux: sudo systemctl start docker"
        warn "Then run this script again"
        exit 1
    else
        success "✅ Docker is running"
    fi
    
    echo ""
fi

# Create environment file if it doesn't exist
if [[ ! -f ".env" ]]; then
    log "📝 Creating environment configuration..."
    
    if [[ -f "env.template" ]]; then
        cp env.template .env
        success "✅ Environment file created from template"
    else
        warn "⚠️  env.template not found, creating basic .env file"
        
        cat > .env << 'EOF'
# Meme Maker Environment Configuration
REDIS_URL=redis://localhost:6379
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=admin12345
AWS_ENDPOINT_URL=http://localhost:9000
S3_BUCKET=clips
ENV=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
WORKER_CONCURRENCY=2
MAX_CLIP_DURATION=180
EOF
        success "✅ Basic environment file created"
    fi
else
    success "✅ Environment file already exists"
fi

echo ""

# Determine which compose file to use
COMPOSE_FILE="docker-compose.yaml"
if [[ "$PRODUCTION_MODE" == "true" ]]; then
    COMPOSE_FILE="infra/production/docker-compose.prod.yml"
    log "🏭 Starting in production mode..."
else
    log "🛠️  Starting in development mode..."
fi

# Check if compose file exists
if [[ ! -f "$COMPOSE_FILE" ]]; then
    error "❌ Docker Compose file not found: $COMPOSE_FILE"
    exit 1
fi

# Determine docker-compose command
DOCKER_COMPOSE_CMD="docker-compose"
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
fi

# Start the application
log "🚀 Starting Meme Maker application..."
warn "This may take a few minutes the first time (downloading images)..."
echo ""

# Stop any existing containers
log "🛑 Stopping any existing containers..."
$DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" down --remove-orphans &> /dev/null || true

# Start the application
log "▶️  Starting application..."
if $DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" up --build -d; then
    success "✅ Application started successfully!"
else
    error "❌ Failed to start application"
    exit 1
fi

echo ""

# Wait for services to be ready
log "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
log "🏥 Checking service health..."

check_url() {
    local name="$1"
    local url="$2"
    
    if curl -s -f "$url" > /dev/null 2>&1; then
        success "✅ $name is running"
        return 0
    else
        warn "⚠️  $name is not yet ready"
        return 1
    fi
}

check_url "Backend API" "http://localhost:8000/health"
check_url "Frontend" "http://localhost:3000"

echo ""

# Display access information
success "🎉 Meme Maker is now running!"
info "================================"
echo ""
info "📱 Access the application:"
info "   🌐 Main App:        http://localhost:3000"
info "   📚 API Docs:        http://localhost:8000/docs"
info "   💾 Storage Admin:   http://localhost:9001"
info "   ❤️  Health Check:   http://localhost:8000/health"
echo ""
info "🔐 MinIO Storage Credentials:"
info "   Username: admin"
info "   Password: admin12345"
echo ""
info "📋 Useful commands:"
info "   View logs:          $DOCKER_COMPOSE_CMD logs -f"
info "   Stop application:   $DOCKER_COMPOSE_CMD down"
info "   Restart:            $DOCKER_COMPOSE_CMD restart"
echo ""
info "🎬 To use the app:"
info "   1. Go to http://localhost:3000"
info "   2. Paste a video URL (YouTube, Instagram, etc.)"
info "   3. Select the segment you want to clip"
info "   4. Click 'Create Clip' and download!"
echo ""

# Try to open the app in browser
if command -v open &> /dev/null; then
    # macOS
    log "🌐 Opening application in your default browser..."
    open "http://localhost:3000" 2>/dev/null || warn "⚠️  Couldn't open browser automatically"
elif command -v xdg-open &> /dev/null; then
    # Linux
    log "🌐 Opening application in your default browser..."
    xdg-open "http://localhost:3000" 2>/dev/null || warn "⚠️  Couldn't open browser automatically"
else
    warn "⚠️  Please visit http://localhost:3000 in your browser"
fi

echo ""
success "Happy clipping! 🎬✂️"

# Show running containers
echo ""
log "📊 Running containers:"
$DOCKER_COMPOSE_CMD -f "$COMPOSE_FILE" ps 