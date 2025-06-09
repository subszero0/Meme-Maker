#!/bin/bash

# 🔥 Firewall Diagnosis and Fix Script
# This script identifies and fixes common firewall issues blocking web access

echo "🔥 Starting firewall diagnosis and fix..."
echo "========================================"

# Function to check if we're running as root/sudo
check_sudo() {
    if [ "$EUID" -ne 0 ]; then
        echo "❌ This script needs to be run with sudo privileges"
        echo "💡 Run: sudo bash scripts/fix-firewall.sh"
        exit 1
    fi
    echo "✅ Running with sudo privileges"
}

# Function to backup current firewall rules
backup_firewall() {
    echo ""
    echo "💾 Backing up current firewall configuration..."
    
    # Backup UFW rules
    if command -v ufw &> /dev/null; then
        ufw status verbose > /tmp/ufw-backup-$(date +%Y%m%d-%H%M%S).txt
        echo "✅ UFW rules backed up to /tmp/"
    fi
    
    # Backup iptables rules
    iptables-save > /tmp/iptables-backup-$(date +%Y%m%d-%H%M%S).txt
    echo "✅ iptables rules backed up to /tmp/"
}

# Function to diagnose current firewall state
diagnose_firewall() {
    echo ""
    echo "🔍 Diagnosing current firewall state..."
    echo "======================================"
    
    # Check UFW status
    if command -v ufw &> /dev/null; then
        echo ""
        echo "📋 UFW Status:"
        ufw status verbose
        
        echo ""
        echo "📋 UFW Rules (numbered):"
        ufw status numbered
    else
        echo "❌ UFW not installed"
    fi
    
    # Check iptables
    echo ""
    echo "📋 iptables INPUT chain:"
    iptables -L INPUT -n -v --line-numbers
    
    echo ""
    echo "📋 iptables FORWARD chain:"
    iptables -L FORWARD -n -v --line-numbers
    
    # Check for Docker iptables rules
    echo ""
    echo "📋 Docker iptables rules:"
    iptables -t nat -L -n -v | grep -E "DOCKER|80|443|8000" || echo "No Docker-related rules found"
}

# Function to check LightSail firewall (if applicable)
check_lightsail_firewall() {
    echo ""
    echo "☁️ Checking if this is a LightSail instance..."
    
    if curl -s --connect-timeout 2 http://169.254.169.254/latest/meta-data/instance-id &>/dev/null; then
        echo "✅ This appears to be a LightSail/AWS instance"
        echo ""
        echo "⚠️  IMPORTANT: LightSail Console Firewall Check Required"
        echo "=================================================="
        echo "1. Go to https://lightsail.aws.amazon.com/"
        echo "2. Click on your instance"
        echo "3. Go to 'Networking' tab"
        echo "4. Check 'Firewall' section"
        echo "5. Ensure these ports are open:"
        echo "   - HTTP (80) - Application: HTTP, Protocol: TCP, Port: 80"
        echo "   - HTTPS (443) - Application: HTTPS, Protocol: TCP, Port: 443"
        echo "   - Custom (8000) - Protocol: TCP, Port: 8000 (if needed)"
        echo ""
        echo "💡 If these ports are not open, add them through the LightSail console"
        echo ""
    else
        echo "ℹ️  Not a LightSail instance or metadata service unavailable"
    fi
}

# Function to fix common firewall issues
fix_firewall() {
    echo ""
    echo "🔧 Applying firewall fixes..."
    echo "============================"
    
    # Check if UFW is installed and enabled
    if command -v ufw &> /dev/null; then
        echo ""
        echo "🔧 Configuring UFW firewall..."
        
        # Allow SSH first (important!)
        ufw allow ssh
        echo "✅ SSH access preserved"
        
        # Allow HTTP and HTTPS
        ufw allow 80/tcp
        ufw allow 443/tcp
        echo "✅ HTTP (80) and HTTPS (443) ports opened"
        
        # Optionally allow backend port (only if needed for direct access)
        read -p "🤔 Do you need direct access to backend port 8000? (y/N): " allow_backend
        if [[ $allow_backend =~ ^[Yy]$ ]]; then
            ufw allow 8000/tcp
            echo "✅ Backend port 8000 opened"
        else
            echo "ℹ️  Backend port 8000 kept internal (recommended)"
        fi
        
        # Enable UFW if not already enabled
        echo "🔧 Enabling UFW..."
        echo "y" | ufw enable
        
        echo ""
        echo "✅ UFW configuration completed"
        echo "📋 Current UFW status:"
        ufw status verbose
        
    else
        echo "❌ UFW not available, configuring iptables directly..."
        
        # Basic iptables rules for HTTP/HTTPS
        iptables -A INPUT -p tcp --dport 22 -j ACCEPT  # Keep SSH
        iptables -A INPUT -p tcp --dport 80 -j ACCEPT  # HTTP
        iptables -A INPUT -p tcp --dport 443 -j ACCEPT # HTTPS
        iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
        iptables -A INPUT -i lo -j ACCEPT  # Allow loopback
        
        echo "✅ Basic iptables rules applied"
    fi
}

# Function to test firewall changes
test_firewall() {
    echo ""
    echo "🧪 Testing firewall configuration..."
    echo "=================================="
    
    # Test local port binding
    echo "🔍 Checking local port binding..."
    netstat -tulpn | grep -E ":80|:443|:8000" | while read line; do
        echo "📍 $line"
    done
    
    # Test external connectivity (from within the server)
    echo ""
    echo "🔍 Testing local HTTP connectivity..."
    if curl -I -m 5 http://localhost 2>/dev/null | head -1; then
        echo "✅ Local HTTP test passed"
    else
        echo "❌ Local HTTP test failed"
    fi
    
    # Check if Caddy is responding
    echo ""
    echo "🔍 Testing Caddy response..."
    if curl -I -m 5 http://localhost:80 2>/dev/null | head -1; then
        echo "✅ Caddy is responding on port 80"
    else
        echo "❌ Caddy is not responding on port 80"
    fi
}

# Function to provide next steps
provide_next_steps() {
    echo ""
    echo "🎯 NEXT STEPS AND VERIFICATION"
    echo "============================="
    echo ""
    echo "1. 🔍 Verify firewall rules are working:"
    echo "   curl -I http://memeit.pro"
    echo "   curl -I https://memeit.pro"
    echo ""
    echo "2. ☁️  If still not working, check LightSail console:"
    echo "   - Go to LightSail console → Your instance → Networking"
    echo "   - Ensure ports 80 and 443 are open in the firewall"
    echo ""
    echo "3. 🐳 Check Docker services are running:"
    echo "   docker-compose ps"
    echo "   docker-compose logs"
    echo ""
    echo "4. 🔧 If services aren't running, restart them:"
    echo "   docker-compose down && docker-compose up -d"
    echo ""
    echo "5. 📋 Check detailed logs:"
    echo "   bash scripts/diagnose-deployment.sh"
    echo ""
    echo "🔄 If issues persist, the problem might be:"
    echo "   - LightSail console firewall settings"
    echo "   - Docker container networking"
    echo "   - Caddy configuration"
    echo "   - SSL certificate issues"
}

# Main execution
main() {
    check_sudo
    backup_firewall
    diagnose_firewall
    check_lightsail_firewall
    
    echo ""
    read -p "🤔 Do you want to apply firewall fixes? (y/N): " proceed
    if [[ $proceed =~ ^[Yy]$ ]]; then
        fix_firewall
        test_firewall
    else
        echo "ℹ️  Skipping firewall fixes"
    fi
    
    provide_next_steps
}

# Run main function
main "$@" 