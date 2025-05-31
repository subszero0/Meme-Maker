#!/bin/bash
set -euo pipefail

# S3 Metrics Verification Script
# Tests S3 metrics exporter and validates alert conditions

# Configuration
PROMETHEUS_URL=${PROMETHEUS_URL:-http://localhost:9090}
S3_EXPORTER_URL=${S3_EXPORTER_URL:-http://localhost:9100}
TEST_TIMEOUT=${TEST_TIMEOUT:-300}  # 5 minutes
VERBOSE=${VERBOSE:-false}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_verbose() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${BLUE}🔍 $1${NC}"
    fi
}

# Check if required tools are available
check_dependencies() {
    log_info "Checking dependencies..."
    
    local missing_deps=()
    
    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
    fi
    
    if ! command -v jq &> /dev/null; then
        missing_deps+=("jq")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_info "Install with: apt-get install curl jq"
        exit 1
    fi
    
    log_success "All dependencies are available"
}

# Test S3 exporter health
test_exporter_health() {
    log_info "Testing S3 metrics exporter health..."
    
    local response
    if response=$(curl -s -w "%{http_code}" "$S3_EXPORTER_URL/health" 2>/dev/null); then
        local http_code="${response: -3}"
        local body="${response%???}"
        
        if [[ "$http_code" == "200" ]]; then
            log_success "S3 exporter is healthy"
            log_verbose "Response: $body"
            return 0
        else
            log_error "S3 exporter health check failed (HTTP $http_code)"
            return 1
        fi
    else
        log_error "Failed to connect to S3 exporter at $S3_EXPORTER_URL"
        return 1
    fi
}

# Test metrics endpoint
test_metrics_endpoint() {
    log_info "Testing S3 metrics endpoint..."
    
    local response
    if response=$(curl -s "$S3_EXPORTER_URL/metrics" 2>/dev/null); then
        # Check for expected metrics
        local expected_metrics=(
            "S3_STORAGE_BYTES"
            "S3_EGRESS_BYTES"
            "S3_METRICS_LAST_UPDATED_TIMESTAMP"
        )
        
        local missing_metrics=()
        for metric in "${expected_metrics[@]}"; do
            if ! echo "$response" | grep -q "^$metric"; then
                missing_metrics+=("$metric")
            fi
        done
        
        if [[ ${#missing_metrics[@]} -eq 0 ]]; then
            log_success "All expected metrics are present"
            
            # Extract metric values for verification
            local storage_bytes
            storage_bytes=$(echo "$response" | grep "^S3_STORAGE_BYTES" | head -1 | awk '{print $2}')
            local egress_bytes
            egress_bytes=$(echo "$response" | grep "^S3_EGRESS_BYTES" | head -1 | awk '{print $2}')
            
            log_verbose "Storage bytes: $storage_bytes"
            log_verbose "Egress bytes: $egress_bytes"
            
            return 0
        else
            log_error "Missing metrics: ${missing_metrics[*]}"
            return 1
        fi
    else
        log_error "Failed to fetch metrics from $S3_EXPORTER_URL/metrics"
        return 1
    fi
}

# Test Prometheus scraping
test_prometheus_scraping() {
    log_info "Testing Prometheus scraping of S3 metrics..."
    
    # Wait a bit for Prometheus to scrape
    sleep 10
    
    local query_url="$PROMETHEUS_URL/api/v1/query"
    
    # Test storage metric
    local storage_response
    if storage_response=$(curl -s "$query_url?query=S3_STORAGE_BYTES" 2>/dev/null); then
        local result_type
        result_type=$(echo "$storage_response" | jq -r '.data.resultType // empty')
        
        if [[ "$result_type" == "vector" ]]; then
            local results_count
            results_count=$(echo "$storage_response" | jq '.data.result | length')
            
            if [[ "$results_count" -gt 0 ]]; then
                log_success "Prometheus is successfully scraping S3 storage metrics"
                
                # Extract values for display
                local storage_value
                storage_value=$(echo "$storage_response" | jq -r '.data.result[0].value[1] // "N/A"')
                log_verbose "Current storage value in Prometheus: $storage_value bytes"
            else
                log_warning "Prometheus has no S3 storage metric data yet"
                return 1
            fi
        else
            log_error "Invalid response format from Prometheus query"
            return 1
        fi
    else
        log_error "Failed to query Prometheus at $PROMETHEUS_URL"
        return 1
    fi
    
    # Test egress metric
    local egress_response
    if egress_response=$(curl -s "$query_url?query=S3_EGRESS_BYTES" 2>/dev/null); then
        local egress_value
        egress_value=$(echo "$egress_response" | jq -r '.data.result[0].value[1] // "N/A"')
        log_verbose "Current egress value in Prometheus: $egress_value bytes"
    fi
}

# Test alert rules
test_alert_rules() {
    log_info "Testing Prometheus alert rules..."
    
    local rules_response
    if rules_response=$(curl -s "$PROMETHEUS_URL/api/v1/rules" 2>/dev/null); then
        # Check for cost-guardrails rule group
        local groups
        groups=$(echo "$rules_response" | jq -r '.data.groups[].name' 2>/dev/null || echo "")
        
        if echo "$groups" | grep -q "cost-guardrails"; then
            log_success "Cost guardrails rule group is loaded"
            
            # Check for specific alerts
            local expected_alerts=(
                "S3StorageTooHigh"
                "S3EgressTooHigh"
                "S3MetricsExporterDown"
                "S3MetricsStale"
            )
            
            local rules_json
            rules_json=$(echo "$rules_response" | jq '.data.groups[] | select(.name == "cost-guardrails") | .rules[].name' 2>/dev/null || echo "")
            
            local missing_alerts=()
            for alert in "${expected_alerts[@]}"; do
                if ! echo "$rules_json" | grep -q "\"$alert\""; then
                    missing_alerts+=("$alert")
                fi
            done
            
            if [[ ${#missing_alerts[@]} -eq 0 ]]; then
                log_success "All expected cost alert rules are present"
            else
                log_warning "Missing alert rules: ${missing_alerts[*]}"
            fi
        else
            log_error "Cost guardrails rule group is not loaded"
            return 1
        fi
    else
        log_error "Failed to fetch rules from Prometheus"
        return 1
    fi
}

# Simulate high usage to test alerts (for development/testing)
simulate_high_usage() {
    if [[ "${1:-}" != "--simulate" ]]; then
        return 0
    fi
    
    log_warning "Simulating high usage conditions for alert testing..."
    
    # This would need to be implemented based on your testing environment
    # For local development with MinIO, you could:
    # 1. Modify the exporter to return high values
    # 2. Use moto/localstack to mock CloudWatch metrics
    # 3. Manually trigger alerts via Prometheus API
    
    log_info "High usage simulation not implemented in this version"
    log_info "To test alerts, modify the exporter mock values or use real AWS with high usage"
}

# Check for firing alerts
check_firing_alerts() {
    log_info "Checking for firing alerts..."
    
    local alerts_response
    if alerts_response=$(curl -s "$PROMETHEUS_URL/api/v1/alerts" 2>/dev/null); then
        local firing_count
        firing_count=$(echo "$alerts_response" | jq '[.data.alerts[] | select(.state == "firing")] | length' 2>/dev/null || echo "0")
        
        if [[ "$firing_count" -gt 0 ]]; then
            log_warning "Found $firing_count firing alerts"
            
            # List firing alerts
            local firing_alerts
            firing_alerts=$(echo "$alerts_response" | jq -r '.data.alerts[] | select(.state == "firing") | .labels.alertname' 2>/dev/null || echo "")
            
            if [[ -n "$firing_alerts" ]]; then
                log_verbose "Firing alerts: $firing_alerts"
            fi
        else
            log_success "No alerts are currently firing"
        fi
    else
        log_error "Failed to fetch alerts from Prometheus"
        return 1
    fi
}

# Main execution
main() {
    echo "🧪 S3 Metrics & Cost Guardrails Verification"
    echo "=============================================="
    echo
    
    log_info "Configuration:"
    log_info "  Prometheus URL: $PROMETHEUS_URL"
    log_info "  S3 Exporter URL: $S3_EXPORTER_URL"
    log_info "  Test Timeout: ${TEST_TIMEOUT}s"
    log_info "  Verbose: $VERBOSE"
    echo
    
    local test_results=()
    
    # Run tests
    if check_dependencies; then
        test_results+=("dependencies:PASS")
    else
        test_results+=("dependencies:FAIL")
    fi
    
    if test_exporter_health; then
        test_results+=("exporter_health:PASS")
    else
        test_results+=("exporter_health:FAIL")
    fi
    
    if test_metrics_endpoint; then
        test_results+=("metrics_endpoint:PASS")
    else
        test_results+=("metrics_endpoint:FAIL")
    fi
    
    if test_prometheus_scraping; then
        test_results+=("prometheus_scraping:PASS")
    else
        test_results+=("prometheus_scraping:FAIL")
    fi
    
    if test_alert_rules; then
        test_results+=("alert_rules:PASS")
    else
        test_results+=("alert_rules:FAIL")
    fi
    
    # Simulate high usage if requested
    simulate_high_usage "$@"
    
    # Check for alerts
    check_firing_alerts
    
    # Summary
    echo
    log_info "Test Results Summary:"
    local passed=0
    local failed=0
    
    for result in "${test_results[@]}"; do
        local test_name="${result%:*}"
        local test_status="${result#*:}"
        
        if [[ "$test_status" == "PASS" ]]; then
            log_success "$test_name: PASSED"
            ((passed++))
        else
            log_error "$test_name: FAILED"
            ((failed++))
        fi
    done
    
    echo
    if [[ $failed -eq 0 ]]; then
        log_success "All tests passed! S3 cost monitoring is working correctly."
        exit 0
    else
        log_error "$failed tests failed, $passed tests passed."
        exit 1
    fi
}

# Handle command line arguments
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  --help, -h        Show this help message"
    echo "  --verbose, -v     Enable verbose output"
    echo "  --simulate        Simulate high usage conditions for testing"
    echo
    echo "Environment Variables:"
    echo "  PROMETHEUS_URL    Prometheus base URL (default: http://localhost:9090)"
    echo "  S3_EXPORTER_URL   S3 exporter base URL (default: http://localhost:9100)"
    echo "  TEST_TIMEOUT      Test timeout in seconds (default: 300)"
    echo "  VERBOSE           Enable verbose output (default: false)"
    echo
    exit 0
fi

if [[ "${1:-}" == "--verbose" || "${1:-}" == "-v" ]]; then
    VERBOSE=true
    shift
fi

main "$@" 