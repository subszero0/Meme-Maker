#!/bin/bash

# 🛠️ Master Deployment Troubleshooting Script
# This script orchestrates diagnosis and fixes for common deployment issues

echo "🛠️ Starting master deployment troubleshooting..."
echo "================================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status="$1"
    local message="$2"
    
    case $status in
        "success") echo -e "${GREEN}✅ $message${NC}" ;;
        "error") echo -e "${RED}❌ $message${NC}" ;;
        "warning") echo -e "${YELLOW}⚠️  $message${NC}" ;;
        "info") echo -e "${BLUE}ℹ️  $message${NC}" ;;
        *) echo "$message" ;;
    esac
}

# Function to check if running with sudo
check_privileges() {
    if [ "$EUID" -ne 0 ]; then
        print_status "warning" "Some diagnostic commands may require sudo privileges"
        print_status "info" "For complete diagnosis, run: sudo bash scripts/troubleshoot-deployment.sh"
        echo ""
    else
        print_status "success" "Running with sudo privileges"
    fi
}

# Function to run comprehensive diagnostics
run_diagnostics() {
    echo ""
    echo "🔍 PHASE 1: COMPREHENSIVE DIAGNOSTICS"
    echo "====================================="
    
    if [ -f "scripts/diagnose-deployment.sh" ]; then
        print_status "info" "Running comprehensive deployment diagnostics..."
        bash scripts/diagnose-deployment.sh
    else
        print_status "error" "Diagnostic script not found"
    fi
}

# Function to analyze and prioritize issues
analyze_issues() {
    echo ""
    echo "🎯 PHASE 2: ISSUE ANALYSIS"
    echo "=========================="
    
    local issues_found=()
    
    # Check if ports are accessible
    if ! nc -z localhost 80 2>/dev/null; then
        issues_found+=("HTTP_PORT_INACCESSIBLE")
        print_status "error" "HTTP port 80 is not accessible"
    fi
    
    if ! nc -z localhost 443 2>/dev/null; then
        issues_found+=("HTTPS_PORT_INACCESSIBLE") 
        print_status "error" "HTTPS port 443 is not accessible"
    fi
    
    # Check if Docker services are running
    if command -v docker &> /dev/null && docker info &> /dev/null; then
        if ! docker-compose ps 2>/dev/null | grep -q "Up"; then
            issues_found+=("DOCKER_SERVICES_DOWN")
            print_status "error" "Docker services are not running properly"
        fi
    else
        issues_found+=("DOCKER_NOT_AVAILABLE")
        print_status "error" "Docker is not available or not running"
    fi
    
    # Check external connectivity
    if ! ping -c 1 8.8.8.8 &>/dev/null; then
        issues_found+=("NO_INTERNET_CONNECTIVITY")
        print_status "error" "No internet connectivity"
    fi
    
    # Check if this is a cloud instance
    if curl -s --connect-timeout 2 http://169.254.169.254/latest/meta-data/instance-id &>/dev/null; then
        issues_found+=("CLOUD_FIREWALL_CHECK_NEEDED")
        print_status "warning" "Cloud instance detected - firewall check needed"
    fi
    
    # Return the issues found for prioritized fixing
    printf '%s\n' "${issues_found[@]}"
}

# Function to apply prioritized fixes
apply_fixes() {
    local issues=("$@")
    
    echo ""
    echo "🔧 PHASE 3: APPLYING FIXES"
    echo "=========================="
    
    for issue in "${issues[@]}"; do
        case $issue in
            "DOCKER_SERVICES_DOWN"|"DOCKER_NOT_AVAILABLE")
                print_status "info" "Fixing Docker service issues..."
                if [ -f "scripts/fix-docker-services.sh" ]; then
                    bash scripts/fix-docker-services.sh
                else
                    print_status "warning" "Docker fix script not found - attempting basic fix"
                    docker-compose down && docker-compose up -d --force-recreate
                fi
                ;;
                
            "HTTP_PORT_INACCESSIBLE"|"HTTPS_PORT_INACCESSIBLE")
                print_status "info" "Fixing firewall issues..."
                if [ "$EUID" -eq 0 ] && [ -f "scripts/fix-firewall.sh" ]; then
                    bash scripts/fix-firewall.sh
                else
                    print_status "warning" "Need sudo privileges to fix firewall"
                    print_status "info" "Run: sudo bash scripts/fix-firewall.sh"
                fi
                ;;
                
            "CLOUD_FIREWALL_CHECK_NEEDED")
                print_status "warning" "Cloud firewall requires manual intervention"
                echo ""
                echo "🌐 Cloud Firewall Configuration Required:"
                echo "========================================="
                echo "1. Go to your cloud provider console (AWS LightSail, etc.)"
                echo "2. Navigate to your instance networking settings"
                echo "3. Ensure these ports are open:"
                echo "   - Port 80 (HTTP)"
                echo "   - Port 443 (HTTPS)"
                echo "   - Port 22 (SSH - don't close this!)"
                echo ""
                ;;
                
            "NO_INTERNET_CONNECTIVITY")
                print_status "error" "Internet connectivity issue requires network admin intervention"
                ;;
        esac
    done
}

# Function to verify fixes
verify_fixes() {
    echo ""
    echo "🧪 PHASE 4: VERIFICATION"
    echo "======================="
    
    local all_good=true
    
    # Test local HTTP connectivity
    if curl -I -m 5 http://localhost 2>/dev/null | head -1; then
        print_status "success" "Local HTTP connectivity restored"
    else
        print_status "error" "Local HTTP still not working"
        all_good=false
    fi
    
    # Test Docker services
    if docker-compose ps 2>/dev/null | grep -q "Up"; then
        print_status "success" "Docker services are running"
    else
        print_status "error" "Docker services still have issues"
        all_good=false
    fi
    
    # Test external connectivity (if we can)
    if command -v dig &> /dev/null; then
        if dig +short memeit.pro | grep -q "13.126.173.223"; then
            print_status "success" "DNS resolution working"
        else
            print_status "warning" "DNS resolution may have issues"
        fi
    fi
    
    if $all_good; then
        print_status "success" "All critical issues appear to be resolved!"
    else
        print_status "warning" "Some issues may still need manual intervention"
    fi
}

# Function to provide final recommendations
provide_final_recommendations() {
    echo ""
    echo "📋 FINAL RECOMMENDATIONS"
    echo "======================="
    echo ""
    echo "1. 🌐 Test external access:"
    echo "   curl -I http://memeit.pro"
    echo "   curl -I https://memeit.pro"
    echo ""
    echo "2. 🔍 Monitor logs for issues:"
    echo "   docker-compose logs -f"
    echo ""
    echo "3. 🔧 If issues persist:"
    echo "   - Check cloud provider firewall settings"
    echo "   - Verify SSL certificate configuration"
    echo "   - Check DNS propagation"
    echo ""
    echo "4. 📞 Get help:"
    echo "   - Review logs: docker-compose logs [service]"
    echo "   - Check health endpoints: curl http://localhost:8000/health"
    echo "   - Verify Caddy config: docker exec [caddy-container] caddy validate"
    echo ""
}

# Main execution
main() {
    check_privileges
    run_diagnostics
    
    echo ""
    echo "Analyzing issues found..."
    
    # Get list of issues
    mapfile -t detected_issues < <(analyze_issues)
    
    if [ ${#detected_issues[@]} -eq 0 ]; then
        print_status "success" "No critical issues detected!"
        verify_fixes
        provide_final_recommendations
        return 0
    fi
    
    echo ""
    echo "🎯 Issues detected: ${#detected_issues[@]}"
    for issue in "${detected_issues[@]}"; do
        echo "   - $issue"
    done
    
    echo ""
    read -p "🤔 Apply automated fixes for detected issues? (y/N): " apply_fixes_choice
    
    if [[ $apply_fixes_choice =~ ^[Yy]$ ]]; then
        apply_fixes "${detected_issues[@]}"
        verify_fixes
    else
        print_status "info" "Skipping automated fixes - manual intervention needed"
    fi
    
    provide_final_recommendations
}

# Run main function
main "$@" 