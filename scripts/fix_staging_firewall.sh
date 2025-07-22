#!/bin/bash
set -e

echo "🔥 FIXING STAGING FIREWALL FOR MONITORING PORTS..."
echo "================================================="

# Function to print colored output
print_status() {
    echo -e "\033[1;34m$1\033[0m"
}

print_success() {
    echo -e "\033[1;32m✅ $1\033[0m"
}

print_error() {
    echo -e "\033[1;31m❌ $1\033[0m"
}

print_warning() {
    echo -e "\033[1;33m⚠️  $1\033[0m"
}

print_status "Step 1: Checking current firewall status..."

# Check UFW status
echo "Current UFW status:"
sudo ufw status numbered || {
    print_warning "UFW might not be installed or enabled"
}

print_status "Step 2: Opening monitoring ports..."

# Open Prometheus port
echo "Opening port 9090 for Prometheus..."
sudo ufw allow 9090/tcp comment "Prometheus monitoring"

# Open Grafana port  
echo "Opening port 3001 for Grafana..."
sudo ufw allow 3001/tcp comment "Grafana monitoring"

# Open Redis Exporter port (optional, for debugging)
echo "Opening port 9121 for Redis Exporter..."
sudo ufw allow 9121/tcp comment "Redis Exporter metrics"

print_success "Firewall rules added"

print_status "Step 3: Checking AWS Lightsail firewall..."

echo ""
print_warning "IMPORTANT: Also check AWS Lightsail Console!"
echo "1. Go to: https://lightsail.aws.amazon.com/"
echo "2. Click on your instance: ip-172-26-5-85"
echo "3. Click 'Networking' tab"
echo "4. Under 'Firewall', click 'Add rule'"
echo "5. Add these rules:"
echo "   - Application: Custom, Protocol: TCP, Port: 9090"
echo "   - Application: Custom, Protocol: TCP, Port: 3001"
echo "   - Application: Custom, Protocol: TCP, Port: 9121"

print_status "Step 4: Testing port accessibility..."

# Test local ports
echo ""
echo "Testing local port accessibility:"
echo "================================"

# Test Prometheus locally
if curl -f http://localhost:9090/-/healthy >/dev/null 2>&1; then
    print_success "Prometheus responding locally (port 9090)"
else
    print_error "Prometheus NOT responding locally (port 9090)"
fi

# Test Grafana locally
if curl -f http://localhost:3001/api/health >/dev/null 2>&1; then
    print_success "Grafana responding locally (port 3001)"
else
    print_error "Grafana NOT responding locally (port 3001)"
fi

# Test Redis Exporter locally
if curl -f http://localhost:9121/metrics >/dev/null 2>&1; then
    print_success "Redis Exporter responding locally (port 9121)"
else
    print_error "Redis Exporter NOT responding locally (port 9121)"
fi

print_status "Step 5: Testing external accessibility..."

# Get external IP
EXTERNAL_IP=$(curl -s ifconfig.me || echo "13.126.173.223")
echo "External IP: $EXTERNAL_IP"

echo ""
echo "Testing external accessibility (this may take a moment)..."

# Test external Prometheus access
if timeout 10 bash -c "</dev/tcp/$EXTERNAL_IP/9090" 2>/dev/null; then
    print_success "Port 9090 is externally accessible"
else
    print_error "Port 9090 NOT externally accessible - check AWS Lightsail firewall"
fi

# Test external Grafana access
if timeout 10 bash -c "</dev/tcp/$EXTERNAL_IP/3001" 2>/dev/null; then
    print_success "Port 3001 is externally accessible"
else
    print_error "Port 3001 NOT externally accessible - check AWS Lightsail firewall"
fi

echo ""
echo "🎉 FIREWALL FIX COMPLETED!"
echo "=========================="
echo ""
echo "📊 Try accessing monitoring now:"
echo "  Prometheus:  http://$EXTERNAL_IP:9090/"
echo "  Grafana:     http://$EXTERNAL_IP:3001/"
echo "    Username: admin"
echo "    Password: staging_admin_2025_secure"
echo ""
echo "🔍 If still not accessible:"
echo "  1. Check AWS Lightsail Console firewall rules"
echo "  2. Wait 2-3 minutes for firewall changes to take effect"
echo "  3. Check container logs: docker-compose logs prometheus grafana"
echo ""
echo "Updated UFW status:"
sudo ufw status numbered 