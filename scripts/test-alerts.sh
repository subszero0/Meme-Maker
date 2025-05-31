#!/bin/bash

# Meme Maker Alert Testing Script
# This script helps simulate various failure conditions to test alerting

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="http://localhost:8000"
PROMETHEUS_URL="http://localhost:9090"
ALERTMANAGER_URL="http://localhost:9093"

echo -e "${BLUE}🧪 Meme Maker Alert Testing Script${NC}"
echo "=================================="

# Function to check if services are running
check_services() {
    echo -e "\n${BLUE}🔍 Checking service availability...${NC}"
    
    # Check Prometheus
    if curl -s -f "${PROMETHEUS_URL}/api/v1/status/buildinfo" > /dev/null; then
        echo -e "✅ Prometheus is running at ${PROMETHEUS_URL}"
    else
        echo -e "❌ Prometheus is not accessible at ${PROMETHEUS_URL}"
        return 1
    fi
    
    # Check Alertmanager
    if curl -s -f "${ALERTMANAGER_URL}/api/v1/status" > /dev/null; then
        echo -e "✅ Alertmanager is running at ${ALERTMANAGER_URL}"
    else
        echo -e "❌ Alertmanager is not accessible at ${ALERTMANAGER_URL}"
        return 1
    fi
    
    # Check Backend
    if curl -s -f "${BACKEND_URL}/health" > /dev/null; then
        echo -e "✅ Backend is running at ${BACKEND_URL}"
    else
        echo -e "❌ Backend is not accessible at ${BACKEND_URL}"
        return 1
    fi
}

# Function to test Slack webhook
test_slack_webhook() {
    echo -e "\n${BLUE}📱 Testing Slack webhook...${NC}"
    
    if [ -z "${ALERT_SLACK_WEBHOOK}" ]; then
        echo -e "❌ ALERT_SLACK_WEBHOOK environment variable not set"
        return 1
    fi
    
    local response=$(curl -s -w "%{http_code}" -o /dev/null -X POST "${ALERT_SLACK_WEBHOOK}" \
        -H "Content-Type: application/json" \
        -d '{"text": "🧪 Test alert from Meme Maker monitoring - Alert system is working!"}')
    
    if [ "$response" = "200" ]; then
        echo -e "✅ Slack webhook test successful"
    else
        echo -e "❌ Slack webhook test failed (HTTP $response)"
        return 1
    fi
}

# Function to check Prometheus rules
check_prometheus_rules() {
    echo -e "\n${BLUE}📋 Checking Prometheus rules...${NC}"
    
    local rules=$(curl -s "${PROMETHEUS_URL}/api/v1/rules" | jq -r '.data.groups[].rules[].alert' 2>/dev/null | sort)
    
    if [ $? -eq 0 ] && [ -n "$rules" ]; then
        echo -e "✅ Prometheus rules loaded:"
        echo "$rules" | while read -r rule; do
            if [ -n "$rule" ] && [ "$rule" != "null" ]; then
                echo -e "  - $rule"
            fi
        done
    else
        echo -e "❌ Failed to fetch Prometheus rules or no rules found"
        return 1
    fi
}

# Function to simulate API downtime
simulate_api_downtime() {
    echo -e "\n${YELLOW}⚠️  Simulating API downtime...${NC}"
    echo "This will stop the backend container for 4 minutes to trigger the API_Uptime_Failure alert"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}🛑 Stopping backend container...${NC}"
        docker stop meme-maker-backend
        
        echo -e "${YELLOW}⏱️  Waiting 4 minutes for alert to trigger...${NC}"
        for i in {240..1}; do
            printf "\rTime remaining: %02d:%02d" $((i/60)) $((i%60))
            sleep 1
        done
        
        echo -e "\n${GREEN}🔄 Restarting backend container...${NC}"
        docker start meme-maker-backend
        
        echo -e "${GREEN}✅ Backend restarted. Check Slack/Email for alerts!${NC}"
    else
        echo "Cancelled."
    fi
}

# Function to simulate high error rate
simulate_high_error_rate() {
    echo -e "\n${YELLOW}⚠️  Simulating high error rate...${NC}"
    echo "This will generate 100 HTTP 500 errors to trigger the API_Error_Rate_High alert"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}🔥 Generating error requests...${NC}"
        
        # Generate errors - targeting a non-existent endpoint to get 404s
        for i in {1..100}; do
            curl -s -o /dev/null "${BACKEND_URL}/non-existent-endpoint" &
            if [ $((i % 10)) -eq 0 ]; then
                echo -n "."
            fi
        done
        wait
        
        echo -e "\n${GREEN}✅ Error generation complete. Monitor Prometheus for alert trigger!${NC}"
        echo "Check: ${PROMETHEUS_URL}/graph?g0.expr=rate(http_requests_total{status!~\"2..\"}[5m])%20%2F%20rate(http_requests_total[5m])"
    else
        echo "Cancelled."
    fi
}

# Function to simulate worker issues
simulate_worker_issues() {
    echo -e "\n${YELLOW}⚠️  Simulating worker issues...${NC}"
    echo "This will stop the worker container for 12 minutes to trigger the Worker_Not_Processing alert"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}🛑 Stopping worker container...${NC}"
        docker stop meme-maker-worker
        
        echo -e "${YELLOW}⏱️  Waiting 12 minutes for alert to trigger...${NC}"
        for i in {720..1}; do
            printf "\rTime remaining: %02d:%02d" $((i/60)) $((i%60))
            sleep 1
        done
        
        echo -e "\n${GREEN}🔄 Restarting worker container...${NC}"
        docker start meme-maker-worker
        
        echo -e "${GREEN}✅ Worker restarted. Check Slack/Email for alerts!${NC}"
    else
        echo "Cancelled."
    fi
}

# Function to check current alerts
check_current_alerts() {
    echo -e "\n${BLUE}🚨 Current active alerts:${NC}"
    
    local alerts=$(curl -s "${ALERTMANAGER_URL}/api/v1/alerts" | jq -r '.data[] | select(.status.state == "active") | .labels.alertname' 2>/dev/null)
    
    if [ $? -eq 0 ] && [ -n "$alerts" ]; then
        echo "$alerts" | while read -r alert; do
            if [ -n "$alert" ] && [ "$alert" != "null" ]; then
                echo -e "  🔥 $alert"
            fi
        done
        
        if [ -z "$(echo "$alerts" | grep -v '^$')" ]; then
            echo -e "  ✅ No active alerts"
        fi
    else
        echo -e "❌ Failed to fetch alerts from Alertmanager"
    fi
}

# Function to show monitoring URLs
show_monitoring_urls() {
    echo -e "\n${BLUE}🔗 Monitoring URLs:${NC}"
    echo -e "  📊 Prometheus: ${PROMETHEUS_URL}"
    echo -e "  📊 Prometheus Rules: ${PROMETHEUS_URL}/rules"
    echo -e "  🚨 Alertmanager: ${ALERTMANAGER_URL}"
    echo -e "  📈 Grafana: http://localhost:3000"
    echo -e "  🏥 Backend Health: ${BACKEND_URL}/health"
    echo -e "  📊 Backend Metrics: ${BACKEND_URL}/metrics"
}

# Main menu
show_menu() {
    echo -e "\n${BLUE}📋 Available Tests:${NC}"
    echo "1. Check service availability"
    echo "2. Test Slack webhook"
    echo "3. Check Prometheus rules"
    echo "4. Check current alerts"
    echo "5. Simulate API downtime (4 min)"
    echo "6. Simulate high error rate"
    echo "7. Simulate worker issues (12 min)"
    echo "8. Show monitoring URLs"
    echo "9. Exit"
}

# Main execution
main() {
    while true; do
        show_menu
        read -p "Select an option (1-9): " choice
        
        case $choice in
            1) check_services ;;
            2) test_slack_webhook ;;
            3) check_prometheus_rules ;;
            4) check_current_alerts ;;
            5) simulate_api_downtime ;;
            6) simulate_high_error_rate ;;
            7) simulate_worker_issues ;;
            8) show_monitoring_urls ;;
            9) echo -e "\n${GREEN}👋 Goodbye!${NC}"; exit 0 ;;
            *) echo -e "\n${RED}❌ Invalid option. Please try again.${NC}" ;;
        esac
    done
}

# Check if required tools are available
if ! command -v curl &> /dev/null; then
    echo -e "${RED}❌ curl is required but not installed${NC}"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠️  jq is not installed. Some features may not work properly.${NC}"
fi

# Start the script
main 