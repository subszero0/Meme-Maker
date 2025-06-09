#!/bin/bash

# 🐳 Docker Services Diagnosis and Fix Script
# This script identifies and fixes Docker networking and service binding issues

echo "🐳 Starting Docker services diagnosis and fix..."
echo "==============================================="

# Function to check Docker status
check_docker_status() {
    echo ""
    echo "🔍 Checking Docker status..."
    echo "==========================="
    
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        echo "❌ Docker daemon is not running"
        echo "💡 Try: sudo systemctl start docker"
        return 1
    fi
    
    echo "✅ Docker is running"
    
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose is not installed"
        return 1
    fi
    
    echo "✅ Docker Compose is available"
    return 0
}

# Function to diagnose container status
diagnose_containers() {
    echo ""
    echo "🔍 Diagnosing container status..."
    echo "==============================="
    
    echo "📋 All containers:"
    docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    echo "📋 Running containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    echo "📋 Docker Compose services:"
    if [ -f "docker-compose.yaml" ] || [ -f "docker-compose.yml" ]; then
        docker-compose ps
    else
        echo "❌ No docker-compose.yaml found"
    fi
}

# Function to check port bindings
check_port_bindings() {
    echo ""
    echo "🔍 Checking port bindings..."
    echo "=========================="
    
    echo "📋 Host port bindings:"
    netstat -tulpn | grep -E ":80|:443|:8000"
    
    echo ""
    echo "📋 Docker port mappings:"
    docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -E "80|443|8000"
    
    echo ""
    echo "🔍 Checking specific service bindings..."
    
    # Check Caddy
    caddy_container=$(docker-compose ps -q caddy 2>/dev/null)
    if [ -n "$caddy_container" ]; then
        echo "📍 Caddy container: $caddy_container"
        docker port $caddy_container 2>/dev/null || echo "❌ No port mappings for Caddy"
    else
        echo "❌ Caddy container not found"
    fi
    
    # Check Backend
    backend_container=$(docker-compose ps -q backend 2>/dev/null)
    if [ -n "$backend_container" ]; then
        echo "📍 Backend container: $backend_container"
        docker port $backend_container 2>/dev/null || echo "❌ No port mappings for Backend"
    else
        echo "❌ Backend container not found"
    fi
}

# Function to check container logs for errors
check_container_logs() {
    echo ""
    echo "🔍 Checking container logs for errors..."
    echo "======================================"
    
    # Check Caddy logs
    echo ""
    echo "📋 Caddy logs (last 20 lines):"
    docker-compose logs --tail=20 caddy 2>/dev/null || echo "❌ Cannot get Caddy logs"
    
    # Check Backend logs
    echo ""
    echo "📋 Backend logs (last 20 lines):"
    docker-compose logs --tail=20 backend 2>/dev/null || echo "❌ Cannot get Backend logs"
    
    # Check for common error patterns
    echo ""
    echo "🔍 Checking for common error patterns..."
    
    if docker-compose logs caddy 2>/dev/null | grep -i "error\|fail\|panic" | tail -5; then
        echo "⚠️  Found errors in Caddy logs"
    else
        echo "✅ No obvious errors in Caddy logs"
    fi
    
    if docker-compose logs backend 2>/dev/null | grep -i "error\|fail\|exception" | tail -5; then
        echo "⚠️  Found errors in Backend logs"
    else
        echo "✅ No obvious errors in Backend logs"
    fi
}

# Function to check network connectivity
check_network_connectivity() {
    echo ""
    echo "🔍 Checking network connectivity..."
    echo "================================="
    
    # Test internal container communication
    caddy_container=$(docker-compose ps -q caddy 2>/dev/null)
    if [ -n "$caddy_container" ]; then
        echo "🔍 Testing Caddy → Backend connectivity:"
        docker exec $caddy_container curl -f -m 5 http://backend:8000/health 2>/dev/null && echo "✅ Caddy can reach Backend" || echo "❌ Caddy cannot reach Backend"
    fi
    
    # Test external accessibility
    echo ""
    echo "🔍 Testing external accessibility:"
    
    # Test HTTP locally
    if curl -I -m 5 http://localhost 2>/dev/null | head -1; then
        echo "✅ HTTP localhost accessible"
    else
        echo "❌ HTTP localhost not accessible"
    fi
    
    # Test HTTP on specific port
    if curl -I -m 5 http://localhost:80 2>/dev/null | head -1; then
        echo "✅ HTTP port 80 accessible"
    else
        echo "❌ HTTP port 80 not accessible"
    fi
    
    # Test backend directly (if exposed)
    if curl -f -m 5 http://localhost:8000/health 2>/dev/null; then
        echo "✅ Backend port 8000 accessible"
    else
        echo "❌ Backend port 8000 not accessible"
    fi
}

# Function to fix common Docker issues
fix_docker_services() {
    echo ""
    echo "🔧 Fixing Docker service issues..."
    echo "================================"
    
    # Stop all services
    echo "🛑 Stopping all services..."
    docker-compose down
    
    # Clean up any orphaned containers
    echo "🧹 Cleaning up orphaned containers..."
    docker system prune -f
    
    # Check for port conflicts
    echo "🔍 Checking for port conflicts..."
    for port in 80 443 8000; do
        if netstat -tulpn | grep ":$port " | grep -v docker; then
            echo "⚠️  Port $port is in use by non-Docker process:"
            netstat -tulpn | grep ":$port "
            echo "💡 You may need to stop the conflicting service"
        fi
    done
    
    # Restart services with fresh containers
    echo "🚀 Starting services with fresh containers..."
    docker-compose up -d --force-recreate
    
    # Wait for services to start
    echo "⏳ Waiting for services to start..."
    sleep 10
    
    # Check if services started successfully
    echo "🔍 Checking service startup..."
    docker-compose ps
}

# Function to validate Caddy configuration
validate_caddy_config() {
    echo ""
    echo "🔍 Validating Caddy configuration..."
    echo "=================================="
    
    if [ -f "Caddyfile" ]; then
        echo "📋 Current Caddyfile:"
        cat Caddyfile
        
        # Validate config if Caddy is running
        caddy_container=$(docker-compose ps -q caddy 2>/dev/null)
        if [ -n "$caddy_container" ]; then
            echo ""
            echo "🔍 Validating Caddy config..."
            docker exec $caddy_container caddy validate --config /etc/caddy/Caddyfile && echo "✅ Caddy config is valid" || echo "❌ Caddy config has errors"
        fi
    else
        echo "❌ Caddyfile not found"
    fi
}

# Function to provide recommendations
provide_recommendations() {
    echo ""
    echo "💡 RECOMMENDATIONS"
    echo "=================="
    echo ""
    echo "Based on the diagnosis, here are the next steps:"
    echo ""
    echo "1. 🔥 Check firewall settings:"
    echo "   sudo bash scripts/fix-firewall.sh"
    echo ""
    echo "2. ☁️  Check LightSail console firewall:"
    echo "   - Ensure ports 80 and 443 are open"
    echo ""
    echo "3. 🔧 If Caddy config errors found:"
    echo "   - Review Caddyfile syntax"
    echo "   - Check SSL certificate paths"
    echo ""
    echo "4. 🐳 If containers keep failing:"
    echo "   - Check individual service logs: docker-compose logs [service]"
    echo "   - Verify environment variables"
    echo "   - Check resource limits"
    echo ""
    echo "5. 📋 Run comprehensive diagnostics:"
    echo "   bash scripts/diagnose-deployment.sh"
}

# Main execution
main() {
    if ! check_docker_status; then
        echo "❌ Docker issues detected. Please fix Docker installation first."
        exit 1
    fi
    
    diagnose_containers
    check_port_bindings
    check_container_logs
    check_network_connectivity
    validate_caddy_config
    
    echo ""
    read -p "🤔 Do you want to restart Docker services? (y/N): " restart_services
    if [[ $restart_services =~ ^[Yy]$ ]]; then
        fix_docker_services
        echo ""
        echo "✅ Services restarted. Testing connectivity..."
        sleep 5
        check_network_connectivity
    fi
    
    provide_recommendations
}

# Run main function
main "$@" 