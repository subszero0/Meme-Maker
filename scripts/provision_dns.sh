#!/bin/bash
# DNS Provisioning Script for Meme Maker Production
# Manages Route 53 DNS records and ACME challenge tokens

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ZONE_ID="${ROUTE53_ZONE_ID:-}"
DOMAIN="memeit.pro"
PRODUCTION_IP="${PRODUCTION_SERVER_IP:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}❌${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS CLI is not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    log_success "Dependencies check passed"
}

validate_zone() {
    log_info "Validating Route 53 hosted zone..."
    
    if [ -z "$ZONE_ID" ]; then
        log_error "ROUTE53_ZONE_ID environment variable is required"
        exit 1
    fi
    
    if ! aws route53 get-hosted-zone --id "$ZONE_ID" &> /dev/null; then
        log_error "Cannot access Route 53 hosted zone: $ZONE_ID"
        exit 1
    fi
    
    log_success "Route 53 zone validation passed"
}

create_production_dns_records() {
    log_info "Creating production DNS records..."
    
    if [ -z "$PRODUCTION_IP" ]; then
        log_error "PRODUCTION_SERVER_IP environment variable is required"
        exit 1
    fi
    
    # Create or update A record for app.memeit.pro
    log_info "Creating A record for app.$DOMAIN -> $PRODUCTION_IP"
    
    cat > /tmp/app-record.json << EOF
{
    "Comment": "Create A record for app.$DOMAIN",
    "Changes": [{
        "Action": "UPSERT",
        "ResourceRecordSet": {
            "Name": "app.$DOMAIN",
            "Type": "A",
            "TTL": 300,
            "ResourceRecords": [{"Value": "$PRODUCTION_IP"}]
        }
    }]
}
EOF
    
    aws route53 change-resource-record-sets \
        --hosted-zone-id "$ZONE_ID" \
        --change-batch file:///tmp/app-record.json
    
    # Create or update CNAME record for www.memeit.pro -> app.memeit.pro
    log_info "Creating CNAME record for www.$DOMAIN -> app.$DOMAIN"
    
    cat > /tmp/www-record.json << EOF
{
    "Comment": "Create CNAME record for www.$DOMAIN",
    "Changes": [{
        "Action": "UPSERT",
        "ResourceRecordSet": {
            "Name": "www.$DOMAIN",
            "Type": "CNAME",
            "TTL": 300,
            "ResourceRecords": [{"Value": "app.$DOMAIN"}]
        }
    }]
}
EOF
    
    aws route53 change-resource-record-sets \
        --hosted-zone-id "$ZONE_ID" \
        --change-batch file:///tmp/www-record.json
    
    # Create or update A record for monitoring.memeit.pro
    log_info "Creating A record for monitoring.$DOMAIN -> $PRODUCTION_IP"
    
    cat > /tmp/monitoring-record.json << EOF
{
    "Comment": "Create A record for monitoring.$DOMAIN",
    "Changes": [{
        "Action": "UPSERT",
        "ResourceRecordSet": {
            "Name": "monitoring.$DOMAIN",
            "Type": "A",
            "TTL": 300,
            "ResourceRecords": [{"Value": "$PRODUCTION_IP"}]
        }
    }]
}
EOF
    
    aws route53 change-resource-record-sets \
        --hosted-zone-id "$ZONE_ID" \
        --change-batch file:///tmp/monitoring-record.json
    
    log_success "Production DNS records created"
}

create_acme_challenge_records() {
    log_info "Creating ACME challenge DNS records..."
    
    # Create placeholder TXT records for ACME challenges (Caddy will update these)
    log_info "Creating TXT record for _acme-challenge.$DOMAIN"
    
    cat > /tmp/acme-record.json << EOF
{
    "Comment": "Create TXT record for ACME challenge",
    "Changes": [{
        "Action": "UPSERT",
        "ResourceRecordSet": {
            "Name": "_acme-challenge.$DOMAIN",
            "Type": "TXT",
            "TTL": 60,
            "ResourceRecords": [{"Value": "\"placeholder-for-acme-challenge\""}]
        }
    }]
}
EOF
    
    aws route53 change-resource-record-sets \
        --hosted-zone-id "$ZONE_ID" \
        --change-batch file:///tmp/acme-record.json
    
    log_success "ACME challenge records created"
}

verify_dns_propagation() {
    log_info "Verifying DNS propagation..."
    
    local records=("app.$DOMAIN" "www.$DOMAIN" "monitoring.$DOMAIN")
    
    for record in "${records[@]}"; do
        log_info "Checking DNS propagation for $record..."
        
        # Wait up to 2 minutes for DNS propagation
        local attempts=0
        local max_attempts=24
        
        while [ $attempts -lt $max_attempts ]; do
            if dig +short "$record" | grep -q "$PRODUCTION_IP\|app.$DOMAIN"; then
                log_success "DNS propagation verified for $record"
                break
            fi
            
            attempts=$((attempts + 1))
            log_info "Waiting for DNS propagation... ($attempts/$max_attempts)"
            sleep 5
        done
        
        if [ $attempts -eq $max_attempts ]; then
            log_warning "DNS propagation check timed out for $record"
        fi
    done
}

setup_route53_logging() {
    log_info "Setting up Route 53 query logging..."
    
    # Create CloudWatch log group for Route 53 queries
    if ! aws logs describe-log-groups --log-group-name-prefix "/aws/route53/queries" | grep -q "/aws/route53/queries"; then
        aws logs create-log-group --log-group-name "/aws/route53/queries"
        log_success "Created CloudWatch log group for Route 53 queries"
    else
        log_info "CloudWatch log group already exists"
    fi
    
    # Enable query logging for the hosted zone
    if ! aws route53 list-query-logging-configs --hosted-zone-id "$ZONE_ID" | grep -q "$ZONE_ID"; then
        aws route53 create-query-logging-config \
            --hosted-zone-id "$ZONE_ID" \
            --cloud-watch-logs-log-group-arn "arn:aws:logs:${AWS_REGION:-us-east-1}:$(aws sts get-caller-identity --query Account --output text):log-group:/aws/route53/queries"
        log_success "Enabled Route 53 query logging"
    else
        log_info "Route 53 query logging already enabled"
    fi
}

cleanup_temp_files() {
    log_info "Cleaning up temporary files..."
    rm -f /tmp/app-record.json /tmp/www-record.json /tmp/monitoring-record.json /tmp/acme-record.json
}

main() {
    log_info "Starting DNS provisioning for Meme Maker production..."
    
    check_dependencies
    validate_zone
    create_production_dns_records
    create_acme_challenge_records
    setup_route53_logging
    verify_dns_propagation
    cleanup_temp_files
    
    log_success "DNS provisioning completed successfully!"
    log_info "Next steps:"
    log_info "1. Deploy the production stack with the new Caddyfile"
    log_info "2. Caddy will automatically obtain wildcard SSL certificates"
    log_info "3. Monitor SSL certificate renewal in Caddy logs"
    log_info "4. Submit HSTS preload request at https://hstspreload.org"
    
    echo
    log_info "DNS Records Created:"
    echo "  app.$DOMAIN -> $PRODUCTION_IP"
    echo "  www.$DOMAIN -> app.$DOMAIN"
    echo "  monitoring.$DOMAIN -> $PRODUCTION_IP"
    echo "  _acme-challenge.$DOMAIN -> (managed by Caddy)"
}

# Handle script interruption
trap cleanup_temp_files EXIT

# Run main function
main "$@" 