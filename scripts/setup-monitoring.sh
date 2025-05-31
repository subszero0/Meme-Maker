#!/bin/bash

# Meme Maker Monitoring Setup Script
# This script helps set up the complete monitoring stack with alerting

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Meme Maker Monitoring Setup${NC}"
echo "================================"

# Check if .env file exists
check_env_file() {
    echo -e "\n${BLUE}📁 Checking environment configuration...${NC}"
    
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
        cp env.template .env
        echo -e "${YELLOW}📝 Please edit .env file with your alerting credentials:${NC}"
        echo -e "  - ALERT_SLACK_WEBHOOK"
        echo -e "  - ALERT_EMAIL_USER"
        echo -e "  - ALERT_EMAIL_PASS"
        echo -e "  - ALERT_EMAIL_RECIPIENT"
        echo ""
        read -p "Press Enter when you've updated the .env file..."
    else
        echo -e "✅ .env file found"
    fi
    
    # Check if alerting variables are set
    source .env 2>/dev/null || true
    
    if [ -z "${ALERT_SLACK_WEBHOOK}" ] || [ "${ALERT_SLACK_WEBHOOK}" = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK" ]; then
        echo -e "${YELLOW}⚠️  ALERT_SLACK_WEBHOOK not configured${NC}"
    else
        echo -e "✅ Slack webhook configured"
    fi
    
    if [ -z "${ALERT_EMAIL_USER}" ] || [ "${ALERT_EMAIL_USER}" = "your-smtp-username" ]; then
        echo -e "${YELLOW}⚠️  Email alerting not configured${NC}"
    else
        echo -e "✅ Email alerting configured"
    fi
}

# Start the monitoring stack
start_monitoring() {
    echo -e "\n${BLUE}🚀 Starting monitoring stack...${NC}"
    
    # Stop existing containers to ensure clean start
    echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
    docker-compose down 2>/dev/null || true
    
    # Start the complete stack
    echo -e "${GREEN}🔄 Starting services...${NC}"
    docker-compose up -d
    
    # Wait for services to be ready
    echo -e "${YELLOW}⏱️  Waiting for services to be ready...${NC}"
    
    # Wait for Prometheus
    echo -n "Waiting for Prometheus..."
    for i in {1..30}; do
        if curl -s -f http://localhost:9090/api/v1/status/buildinfo > /dev/null 2>&1; then
            echo -e " ${GREEN}✅${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    # Wait for Alertmanager
    echo -n "Waiting for Alertmanager..."
    for i in {1..30}; do
        if curl -s -f http://localhost:9093/api/v1/status > /dev/null 2>&1; then
            echo -e " ${GREEN}✅${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    # Wait for Backend
    echo -n "Waiting for Backend..."
    for i in {1..30}; do
        if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
            echo -e " ${GREEN}✅${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
}

# Verify monitoring configuration
verify_monitoring() {
    echo -e "\n${BLUE}🔍 Verifying monitoring configuration...${NC}"
    
    # Check Prometheus rules
    echo -n "Checking Prometheus rules..."
    local rules=$(curl -s http://localhost:9090/api/v1/rules 2>/dev/null | jq -r '.data.groups[].rules[].alert' 2>/dev/null | grep -c "API_Uptime_Failure\|API_Error_Rate_High" 2>/dev/null || echo "0")
    
    if [ "$rules" -ge 2 ]; then
        echo -e " ${GREEN}✅ ($rules alerting rules loaded)${NC}"
    else
        echo -e " ${RED}❌ (Expected 2+ rules, found $rules)${NC}"
    fi
    
    # Check Alertmanager configuration
    echo -n "Checking Alertmanager configuration..."
    if curl -s http://localhost:9093/api/v1/status 2>/dev/null | jq -r '.data.configYAML' | grep -q "slack_configs" 2>/dev/null; then
        echo -e " ${GREEN}✅${NC}"
    else
        echo -e " ${RED}❌${NC}"
    fi
    
    # Check if containers are running
    echo -e "\n${BLUE}📦 Container status:${NC}"
    docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
}

# Show monitoring URLs
show_urls() {
    echo -e "\n${BLUE}🔗 Monitoring URLs:${NC}"
    echo -e "  📊 Prometheus: http://localhost:9090"
    echo -e "  🚨 Alertmanager: http://localhost:9093"
    echo -e "  📈 Grafana: http://localhost:3000 (admin/admin)"
    echo -e "  🏥 Backend Health: http://localhost:8000/health"
    echo -e "  📊 Backend Metrics: http://localhost:8000/metrics"
    echo -e "  🧪 Test Alerts: ./scripts/test-alerts.sh"
}

# Test basic functionality
test_basic_functionality() {
    echo -e "\n${BLUE}🧪 Testing basic functionality...${NC}"
    
    # Test Slack webhook if configured
    if [ -n "${ALERT_SLACK_WEBHOOK}" ] && [ "${ALERT_SLACK_WEBHOOK}" != "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK" ]; then
        echo -n "Testing Slack webhook..."
        local response=$(curl -s -w "%{http_code}" -o /dev/null -X POST "${ALERT_SLACK_WEBHOOK}" \
            -H "Content-Type: application/json" \
            -d '{"text": "🎉 Meme Maker monitoring setup complete! Alert system is ready."}' 2>/dev/null)
        
        if [ "$response" = "200" ]; then
            echo -e " ${GREEN}✅${NC}"
        else
            echo -e " ${YELLOW}⚠️  (HTTP $response)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Slack webhook not configured - skipping test${NC}"
    fi
    
    # Generate some test metrics
    echo -n "Generating test metrics..."
    for i in {1..5}; do
        curl -s -o /dev/null http://localhost:8000/health &
    done
    wait
    echo -e " ${GREEN}✅${NC}"
}

# Main execution
main() {
    check_env_file
    start_monitoring
    verify_monitoring
    test_basic_functionality
    show_urls
    
    echo -e "\n${GREEN}🎉 Monitoring setup complete!${NC}"
    echo -e "\n${BLUE}📋 Next steps:${NC}"
    echo -e "  1. Visit Prometheus (http://localhost:9090) to check if rules are loaded"
    echo -e "  2. Visit Alertmanager (http://localhost:9093) to verify configuration"
    echo -e "  3. Run './scripts/test-alerts.sh' to test alert conditions"
    echo -e "  4. Configure Grafana dashboards at http://localhost:3000"
    echo -e "\n${YELLOW}💡 Tip: Check docs/monitoring.md for detailed troubleshooting guide${NC}"
}

# Check if required tools are available
if ! command -v curl &> /dev/null; then
    echo -e "${RED}❌ curl is required but not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose is required but not installed${NC}"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠️  jq is not installed. Some features may not work properly.${NC}"
fi

# Start the setup
main 