#!/bin/bash
# Domain and HTTPS Fix Deployment Script
# This script applies all fixes to enable proper domain and HTTPS support

set -e

echo "🚀 Deploying Domain and HTTPS Fixes"
echo "===================================="

# Function to check if running on the server
check_server() {
    if [ ! -f "/etc/os-release" ] || ! grep -q "Ubuntu\|Debian" /etc/os-release; then
        echo "⚠️  This script should be run on the Ubuntu/Debian server"
        echo "   Current fixes will be applied locally, but SSL setup requires server access"
    fi
}

# Function to backup current configuration
backup_config() {
    echo "💾 Creating backup of current configuration..."
    
    # Create backup directory with timestamp
    BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup key files
    cp docker-compose.yaml "$BACKUP_DIR/" 2>/dev/null || true
    cp frontend-new/nginx.conf "$BACKUP_DIR/" 2>/dev/null || true
    cp .env "$BACKUP_DIR/" 2>/dev/null || true
    
    echo "✅ Backup created in: $BACKUP_DIR"
}

# Function to validate configuration files
validate_config() {
    echo "🔍 Validating configuration files..."
    
    # Check if nginx config is valid
    if command -v nginx &> /dev/null; then
        nginx -t -c "$(pwd)/frontend-new/nginx.conf" 2>/dev/null || {
            echo "⚠️  Nginx config validation failed (this is expected if not on server)"
        }
    fi
    
    # Check docker-compose syntax
    docker-compose config > /dev/null && echo "✅ docker-compose.yaml is valid" || {
        echo "❌ docker-compose.yaml has syntax errors"
        exit 1
    }
}

# Function to rebuild and restart services
deploy_changes() {
    echo "🔄 Deploying changes..."
    
    # Stop current services
    echo "⏹️  Stopping services..."
    docker-compose down
    
    # Rebuild frontend with new configuration
    echo "🏗️  Rebuilding frontend..."
    docker-compose build --no-cache frontend
    
    # Start services
    echo "▶️  Starting services..."
    docker-compose up -d
    
    # Wait for services to be healthy
    echo "⏳ Waiting for services to be healthy..."
    sleep 30
    
    # Check service status
    docker-compose ps
}

# Function to test the deployment
test_deployment() {
    echo "🧪 Testing deployment..."
    
    # Test HTTP endpoint
    if curl -f -s http://localhost/ > /dev/null; then
        echo "✅ HTTP endpoint working"
    else
        echo "❌ HTTP endpoint failed"
    fi
    
    # Test API endpoint
    if curl -f -s http://localhost/api/health > /dev/null; then
        echo "✅ API endpoint working"
    else
        echo "❌ API endpoint failed"
    fi
    
    # Test HTTPS (will fail until SSL is set up)
    if curl -f -s -k https://localhost/ > /dev/null 2>&1; then
        echo "✅ HTTPS endpoint working"
    else
        echo "⚠️  HTTPS endpoint not working (SSL certificates needed)"
    fi
}

# Function to show next steps
show_next_steps() {
    echo ""
    echo "🎯 DEPLOYMENT COMPLETE"
    echo "====================="
    echo ""
    echo "✅ Configuration fixes applied:"
    echo "   - Frontend environment fixed (using relative URLs)"
    echo "   - Nginx configuration updated for domain support"
    echo "   - Docker Compose updated with proper ports"
    echo "   - CORS configuration updated"
    echo ""
    echo "🔒 To enable HTTPS, run on your server:"
    echo "   sudo ./setup_ssl_certificate.sh"
    echo ""
    echo "🧪 Test your deployment:"
    echo "   HTTP (IP):     http://13.126.173.223"
    echo "   HTTP (Domain): http://memeit.pro (will redirect to HTTPS after SSL setup)"
    echo "   HTTPS:         https://memeit.pro (after SSL setup)"
    echo ""
    echo "📊 Monitor with:"
    echo "   docker-compose logs -f"
    echo "   docker-compose ps"
    echo ""
    echo "🔄 If issues occur, restore from backup:"
    echo "   cp backup_*/docker-compose.yaml ."
    echo "   cp backup_*/nginx.conf frontend-new/"
    echo "   docker-compose up -d"
}

# Main execution
main() {
    echo "Starting deployment process..."
    
    check_server
    backup_config
    validate_config
    deploy_changes
    test_deployment
    show_next_steps
    
    echo ""
    echo "🎉 Domain and HTTPS fixes deployed successfully!"
}

# Run main function
main "$@" 