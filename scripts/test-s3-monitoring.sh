#!/bin/bash
set -euo pipefail

# Simple S3 Monitoring Integration Test
# Tests the complete integration between S3 exporter, Prometheus, and Alertmanager

# Configuration
PROMETHEUS_URL=${PROMETHEUS_URL:-http://localhost:9090}
ALERTMANAGER_URL=${ALERTMANAGER_URL:-http://localhost:9093}
S3_EXPORTER_URL=${S3_EXPORTER_URL:-http://localhost:9100}

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧪 S3 Cost Monitoring Integration Test${NC}"
echo "========================================"

# Test 1: S3 Exporter Health
echo -n "1. S3 Exporter Health: "
if curl -s -f "$S3_EXPORTER_URL/health" > /dev/null; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL${NC}"
    exit 1
fi

# Test 2: S3 Metrics Available
echo -n "2. S3 Metrics Available: "
if curl -s "$S3_EXPORTER_URL/metrics" | grep -q "S3_STORAGE_BYTES\|S3_EGRESS_BYTES"; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL${NC}"
    exit 1
fi

# Test 3: Prometheus Scraping S3 Metrics
echo -n "3. Prometheus Scraping: "
sleep 5  # Wait for scrape
if curl -s "$PROMETHEUS_URL/api/v1/query?query=S3_STORAGE_BYTES" | jq -r '.data.result[0].value[1] // empty' | grep -q '^[0-9]'; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL${NC}"
    exit 1
fi

# Test 4: Cost Guardrail Rules Loaded
echo -n "4. Cost Guardrail Rules: "
if curl -s "$PROMETHEUS_URL/api/v1/rules" | jq -r '.data.groups[] | select(.name == "cost-guardrails") | .rules[].alert' | grep -q "S3StorageTooHigh\|S3EgressTooHigh"; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL${NC}"
    exit 1
fi

# Test 5: Alertmanager Configuration
echo -n "5. Alertmanager Config: "
if curl -s "$ALERTMANAGER_URL/api/v1/status" | jq -r '.data.configYAML' | grep -q "warning-alerts"; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL${NC}"
    exit 1
fi

echo
echo -e "${GREEN}🎉 All tests passed! S3 cost monitoring is working correctly.${NC}"
echo
echo -e "${BLUE}📊 Current S3 Metrics:${NC}"

# Show current values
STORAGE=$(curl -s "$S3_EXPORTER_URL/metrics" | grep "^S3_STORAGE_BYTES" | head -1 | awk '{print $2}')
EGRESS=$(curl -s "$S3_EXPORTER_URL/metrics" | grep "^S3_EGRESS_BYTES" | head -1 | awk '{print $2}')

echo "  Storage: $(echo "$STORAGE" | numfmt --to=iec-i --suffix=B 2>/dev/null || echo "$STORAGE bytes")"
echo "  Egress:  $(echo "$EGRESS" | numfmt --to=iec-i --suffix=B 2>/dev/null || echo "$EGRESS bytes")"
echo
echo -e "${BLUE}🔗 Monitoring URLs:${NC}"
echo "  S3 Metrics: $S3_EXPORTER_URL/metrics"
echo "  Prometheus: $PROMETHEUS_URL"
echo "  Alertmanager: $ALERTMANAGER_URL" 