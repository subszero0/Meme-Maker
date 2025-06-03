#!/bin/bash
# Production Deployment Script for Meme Maker
# Deploys the application to Lightsail using blue-green deployment strategy

set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================

# Default values - override with environment variables
LIGHTSAIL_IP="${LIGHTSAIL_IP:-}"
LIGHTSAIL_USER="${LIGHTSAIL_USER:-ubuntu}"
GITHUB_REPO="${GITHUB_REPO:-}"
DEPLOY_KEY="${DEPLOY_KEY:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

check_prerequisites() {
    log "🔍 Checking prerequisites..."
    
    # Check if .env.prod exists
    if [[ ! -f ".env.prod" ]]; then
        error ".env.prod file not found. Please create it first using the AWS provisioning guide."
    fi
    
    # Check for required commands
    command -v ssh >/dev/null 2>&1 || error "ssh command not found"
    command -v scp >/dev/null 2>&1 || error "scp command not found"
    command -v git >/dev/null 2>&1 || error "git command not found"
    
    success "✅ Prerequisites check passed"
}

get_config() {
    log "⚙️ Getting configuration..."
    
    # Get Lightsail IP if not provided
    if [[ -z "$LIGHTSAIL_IP" ]]; then
        echo "Enter your Lightsail server IP address:"
        read -r LIGHTSAIL_IP
    fi
    
    # Get GitHub repository if not provided
    if [[ -z "$GITHUB_REPO" ]]; then
        GITHUB_REPO=$(git remote get-url origin 2>/dev/null | sed 's/.*[\/:]//g' | sed 's/.git$//' || echo "")
        if [[ -z "$GITHUB_REPO" ]]; then
            echo "Enter your GitHub repository (e.g., username/meme-maker):"
            read -r GITHUB_REPO
        fi
    fi
    
    # Get current git commit SHA
    GIT_SHA=$(git rev-parse HEAD)
    
    log "Configuration:"
    echo "  Lightsail IP: $LIGHTSAIL_IP"
    echo "  GitHub Repo: $GITHUB_REPO"
    echo "  Git SHA: $GIT_SHA"
    echo "  User: $LIGHTSAIL_USER"
}

test_ssh_connection() {
    log "🔗 Testing SSH connection to $LIGHTSAIL_IP..."
    
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$LIGHTSAIL_USER@$LIGHTSAIL_IP" exit 2>/dev/null; then
        success "✅ SSH connection successful"
    else
        error "❌ Cannot connect to $LIGHTSAIL_IP. Please check your SSH key and server status."
    fi
}

deploy_code() {
    log "📦 Deploying code to Lightsail..."
    
    # Commands to run on the remote server
    ssh "$LIGHTSAIL_USER@$LIGHTSAIL_IP" bash << EOF
        set -euo pipefail
        
        echo "🏠 Setting up deployment directory..."
        cd /home/$LIGHTSAIL_USER
        
        # Clone or update repository
        if [[ -d "meme-maker" ]]; then
            echo "📁 Repository exists, updating..."
            cd meme-maker
            git fetch origin
            git reset --hard origin/main
        else
            echo "📥 Cloning repository..."
            git clone https://github.com/$GITHUB_REPO.git meme-maker
            cd meme-maker
        fi
        
        echo "✅ Code deployment completed"
        echo "📍 Current directory: \$(pwd)"
        echo "📋 Current commit: \$(git rev-parse HEAD)"
EOF
    
    success "✅ Code deployed successfully"
}

transfer_env_file() {
    log "📄 Transferring .env.prod to server..."
    
    scp .env.prod "$LIGHTSAIL_USER@$LIGHTSAIL_IP:/home/$LIGHTSAIL_USER/meme-maker/.env.prod"
    
    success "✅ Environment file transferred"
}

setup_docker() {
    log "🐳 Setting up Docker environment..."
    
    ssh "$LIGHTSAIL_USER@$LIGHTSAIL_IP" bash << EOF
        set -euo pipefail
        cd /home/$LIGHTSAIL_USER/meme-maker
        
        echo "🔧 Creating necessary directories..."
        sudo mkdir -p /opt/meme-data
        sudo chown $LIGHTSAIL_USER:$LIGHTSAIL_USER /opt/meme-data
        mkdir -p logs/deployments
        
        echo "⬇️ Pulling Docker images..."
        docker compose -f infra/production/docker-compose.prod.yml --env-file .env.prod pull
        
        echo "✅ Docker setup completed"
EOF
    
    success "✅ Docker environment ready"
}

run_blue_green_deployment() {
    log "🚀 Running blue-green deployment..."
    
    ssh "$LIGHTSAIL_USER@$LIGHTSAIL_IP" bash << EOF
        set -euo pipefail
        cd /home/$LIGHTSAIL_USER/meme-maker
        
        echo "🎯 Starting blue-green deployment with SHA: $GIT_SHA"
        bash scripts/promote_to_prod.sh $GIT_SHA
        
        echo "✅ Blue-green deployment completed"
EOF
    
    success "✅ Blue-green deployment completed"
}

verify_deployment() {
    log "🔍 Verifying deployment..."
    
    # Wait a moment for services to stabilize
    sleep 10
    
    # Test health endpoint
    log "Testing health endpoint..."
    if curl -fsSL --max-time 30 "https://$LIGHTSAIL_IP/health" | grep -q "ok"; then
        success "✅ Health endpoint responding"
    else
        warn "⚠️ Health endpoint test failed - checking if services are still starting..."
        sleep 30
        if curl -fsSL --max-time 30 "https://$LIGHTSAIL_IP/health" | grep -q "ok"; then
            success "✅ Health endpoint responding (after retry)"
        else
            error "❌ Health endpoint not responding"
        fi
    fi
    
    # Test API documentation
    log "Testing API documentation..."
    if curl -fsSL --max-time 30 "https://$LIGHTSAIL_IP/docs" | grep -q "Swagger"; then
        success "✅ API documentation accessible"
    else
        warn "⚠️ API documentation test inconclusive"
    fi
    
    # Test monitoring (expect basic auth prompt)
    log "Testing monitoring endpoint..."
    if curl -fsSL --max-time 30 "https://monitoring.$LIGHTSAIL_IP/grafana" -w "%{http_code}" | grep -q "401\|200"; then
        success "✅ Monitoring endpoint accessible (basic auth working)"
    else
        warn "⚠️ Monitoring endpoint test inconclusive"
    fi
}

cleanup_old_images() {
    log "🧹 Cleaning up old Docker images..."
    
    ssh "$LIGHTSAIL_USER@$LIGHTSAIL_IP" bash << EOF
        echo "🗑️ Pruning unused Docker images..."
        docker image prune -f
        echo "📊 Current Docker disk usage:"
        docker system df
EOF
    
    success "✅ Cleanup completed"
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    log "🚀 Starting Meme Maker Production Deployment"
    log "============================================"
    
    # Step 1: Prerequisites
    check_prerequisites
    
    # Step 2: Configuration
    get_config
    
    # Step 3: Test connection
    test_ssh_connection
    
    # Step 4: Deploy code
    deploy_code
    
    # Step 5: Transfer environment file
    transfer_env_file
    
    # Step 6: Setup Docker
    setup_docker
    
    # Step 7: Run blue-green deployment
    run_blue_green_deployment
    
    # Step 8: Verify deployment
    verify_deployment
    
    # Step 9: Cleanup
    cleanup_old_images
    
    log ""
    success "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!"
    log ""
    log "============================================"
    log "🌐 Your application is now live at:"
    log "   • Main site: https://$LIGHTSAIL_IP"
    log "   • API docs: https://$LIGHTSAIL_IP/docs"
    log "   • Health: https://$LIGHTSAIL_IP/health"
    log "   • Monitoring: https://monitoring.$LIGHTSAIL_IP/grafana"
    log "============================================"
    log ""
    log "📋 Post-deployment checklist:"
    echo "  [ ] Test video upload and processing"
    echo "  [ ] Check monitoring dashboards"
    echo "  [ ] Verify SSL certificates"
    echo "  [ ] Test rate limiting"
    echo "  [ ] Check log aggregation"
    log ""
    log "🔧 Useful commands:"
    echo "  ssh $LIGHTSAIL_USER@$LIGHTSAIL_IP"
    echo "  docker ps"
    echo "  docker logs meme-prod-backend"
    echo "  docker logs meme-prod-worker"
}

# Run main function
main "$@" 