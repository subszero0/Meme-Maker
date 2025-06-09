#!/bin/bash

# 🔍 Comprehensive Deployment Diagnostic Script
# This script provides detailed analysis of deployment issues

echo "🚀 Starting comprehensive deployment diagnostics..."
echo "=================================================="

# Function to check command availability
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 is not available"
        return 1
    fi
    echo "✅ $1 is available"
    return 0
}

# Function to run command with error handling
run_check() {
    local description="$1"
    local command="$2"
    
    echo ""
    echo "🔍 $description"
    echo "Command: $command"
    echo "---"
    
    if eval "$command"; then
        echo "✅ $description: SUCCESS"
    else
        echo "❌ $description: FAILED (exit code: $?)"
    fi
}

# 1. System Information
echo ""
echo "📊 SYSTEM INFORMATION"
echo "===================="
run_check "Check OS version" "cat /etc/os-release | head -3"
run_check "Check system resources" "free -h && df -h /"
run_check "Check current user" "whoami && id"

# 2. Network Diagnostics
echo ""
echo "🌐 NETWORK DIAGNOSTICS"
echo "====================="
run_check "Check network interfaces" "ip addr show | grep -E 'inet|UP|DOWN'"
run_check "Check default gateway" "ip route | grep default"
run_check "Check DNS resolution for memeit.pro" "nslookup memeit.pro"
run_check "Check external connectivity" "ping -c 2 8.8.8.8"

# 3. Port and Service Analysis
echo ""
echo "🔌 PORT AND SERVICE ANALYSIS"
echo "============================"
run_check "Check listening ports" "netstat -tulpn | grep LISTEN"
run_check "Check processes using ports 80, 443, 8000" "ss -tulpn | grep -E ':80|:443|:8000'"
run_check "Check if services are binding to correct interfaces" "netstat -an | grep -E ':80|:443|:8000'"

# 4. Docker Analysis
echo ""
echo "🐳 DOCKER ANALYSIS"
echo "=================="
if check_command docker; then
    run_check "Check Docker daemon status" "systemctl status docker --no-pager -l"
    run_check "List running containers" "docker ps -a"
    run_check "Check container logs (last 20 lines)" "docker-compose logs --tail=20"
    run_check "Check container networking" "docker network ls && docker inspect $(docker-compose ps -q) | grep -A 10 NetworkSettings"
    run_check "Check docker-compose services" "docker-compose ps"
else
    echo "❌ Docker not available"
fi

# 5. Firewall Analysis
echo ""
echo "🔥 FIREWALL ANALYSIS"
echo "==================="
run_check "Check UFW status" "ufw status verbose"
run_check "Check iptables rules" "iptables -L -n -v"
run_check "Check if UFW is blocking connections" "ufw status numbered"

# 6. Caddy Analysis
echo ""
echo "📋 CADDY ANALYSIS"
echo "================="
if [ -f "Caddyfile" ]; then
    run_check "Show Caddy configuration" "cat Caddyfile"
    run_check "Validate Caddy configuration" "docker exec \$(docker-compose ps -q caddy) caddy validate --config /etc/caddy/Caddyfile"
    run_check "Check Caddy logs" "docker-compose logs caddy --tail=50"
else
    echo "❌ Caddyfile not found"
fi

# 7. SSL Certificate Analysis
echo ""
echo "🔒 SSL CERTIFICATE ANALYSIS"
echo "==========================="
run_check "Check SSL certificate status" "echo | timeout 10 openssl s_client -connect memeit.pro:443 -servername memeit.pro 2>/dev/null | openssl x509 -noout -dates"
run_check "Check Let's Encrypt certificate directory" "ls -la /etc/letsencrypt/live/ 2>/dev/null || echo 'Let\\'s Encrypt directory not found'"

# 8. Backend Service Analysis
echo ""
echo "🔧 BACKEND SERVICE ANALYSIS"
echo "==========================="
run_check "Check FastAPI backend container" "docker-compose logs backend --tail=30"
run_check "Test backend health internally" "curl -f http://localhost:8000/health 2>/dev/null || echo 'Backend health check failed'"
run_check "Test backend from container network" "docker exec \$(docker-compose ps -q caddy) curl -f http://backend:8000/health 2>/dev/null || echo 'Backend not reachable from Caddy'"

# 9. External Connectivity Test
echo ""
echo "🌍 EXTERNAL CONNECTIVITY TEST"
echo "============================="
run_check "Test HTTP connectivity externally" "curl -I -m 10 http://memeit.pro 2>/dev/null || echo 'HTTP connection failed'"
run_check "Test HTTPS connectivity externally" "curl -I -m 10 https://memeit.pro 2>/dev/null || echo 'HTTPS connection failed'"

# 10. LightSail Specific Checks
echo ""
echo "☁️ LIGHTSAIL SPECIFIC CHECKS"
echo "============================"
run_check "Check if this is a LightSail instance" "curl -s http://169.254.169.254/latest/meta-data/instance-id 2>/dev/null && echo 'This is an AWS instance'"
run_check "Get instance metadata" "curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null && echo ' (Public IP)'"

echo ""
echo "🎯 DIAGNOSTIC SUMMARY"
echo "====================="
echo "1. Check the firewall configuration above"
echo "2. Verify Docker containers are running and properly networked"
echo "3. Ensure Caddy is binding to 0.0.0.0:80 and 0.0.0.0:443"
echo "4. Check SSL certificate generation logs"
echo "5. Verify backend service is accessible from Caddy container"
echo ""
echo "🔍 Run 'docker-compose logs' for more detailed service logs"
echo "🔍 Check LightSail console for firewall/networking settings"
echo "" 