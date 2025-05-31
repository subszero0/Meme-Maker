#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Final Pre-Launch Review...${NC}"

# Create reports directory
mkdir -p reports

# Generate unique report filename with timestamp and git commit
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
REPORT_FILE="reports/final-review-${TIMESTAMP}-${GIT_SHA}.md"

echo -e "${BLUE}📊 Report will be saved to: ${REPORT_FILE}${NC}"

# Ensure services are running for testing
echo -e "${BLUE}🔧 Checking if services are running...${NC}"
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${YELLOW}⚠️  Backend not running. Starting services...${NC}"
    docker-compose up -d
    echo "⏳ Waiting for services to be ready..."
    sleep 10
    
    # Wait for backend to be ready
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null; then
            echo -e "${GREEN}✅ Backend is ready${NC}"
            break
        fi
        echo "   Waiting for backend... ($i/30)"
        sleep 2
    done
fi

# Install lighthouse CLI if not present
if ! command -v lhci &> /dev/null; then
    echo -e "${YELLOW}📦 Installing Lighthouse CI...${NC}"
    npm install -g @lhci/cli
fi

# Install axe CLI if not present
if ! command -v axe &> /dev/null; then
    echo -e "${YELLOW}📦 Installing axe-core CLI...${NC}"
    npm install -g @axe-core/cli
fi

# Change to frontend directory for most operations
cd frontend

echo -e "${BLUE}🏗️  Building frontend for testing...${NC}"
npm run build

# Start local server for testing
echo -e "${BLUE}🌐 Starting local server...${NC}"
npm run start &
SERVER_PID=$!
sleep 5

# Function to cleanup on exit
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    kill $SERVER_PID 2>/dev/null || true
    cd ..
}
trap cleanup EXIT

# 1. Lighthouse Performance Audit
echo -e "${BLUE}🚀 Running Lighthouse Performance Audit...${NC}"
npx lhci autorun \
    --upload.target=filesystem \
    --upload.outputDir=../reports/lighthouse \
    --collect.url=http://localhost:3000 \
    --collect.url=http://localhost:3000/trim \
    --collect.settings.chromeFlags="--no-sandbox --headless" \
    || echo -e "${RED}❌ Lighthouse audit failed${NC}"

# 2. Accessibility Audit with axe-core
echo -e "${BLUE}♿ Running Accessibility Audit...${NC}"
npx axe \
    http://localhost:3000 \
    http://localhost:3000/trim \
    --tags wcag2a,wcag2aa \
    --save ../reports/axe.json \
    --exit \
    || echo -e "${RED}❌ Accessibility audit failed${NC}"

# 3. Bundle Size Audit
echo -e "${BLUE}📦 Running Bundle Size Audit...${NC}"
npm run audit:bundle > ../reports/bundle-audit.log 2>&1 || echo -e "${RED}❌ Bundle audit failed${NC}"

# 4. Security Headers Check
echo -e "${BLUE}🔒 Checking Security Headers...${NC}"
curl -I http://localhost:3000 > ../reports/security-headers.log 2>&1 || echo -e "${RED}❌ Security headers check failed${NC}"

# 5. Performance API Check
echo -e "${BLUE}⚡ Testing API Performance...${NC}"
cd ..
curl -o reports/api-health.json -w "@curl-format.txt" http://localhost:8000/health > reports/api-performance.log 2>&1 || echo -e "${RED}❌ API performance check failed${NC}"

# Create curl format file if it doesn't exist
cat > curl-format.txt << 'EOF'
{
  "time_namelookup": %{time_namelookup},
  "time_connect": %{time_connect},
  "time_appconnect": %{time_appconnect},
  "time_pretransfer": %{time_pretransfer},
  "time_redirect": %{time_redirect},
  "time_starttransfer": %{time_starttransfer},
  "time_total": %{time_total},
  "speed_download": %{speed_download},
  "speed_upload": %{speed_upload}
}
EOF

# 6. Cross-browser compatibility check
echo -e "${BLUE}🌐 Checking Cross-browser Compatibility...${NC}"
cd frontend
npx cypress run --browser chrome --headless > ../reports/cypress-chrome.log 2>&1 || echo -e "${RED}❌ Chrome tests failed${NC}"

# 7. Generate consolidated report
echo -e "${BLUE}📝 Generating Final Report...${NC}"
cd ..
node scripts/merge-review-reports.js > "$REPORT_FILE"

echo -e "${GREEN}✅ Final Review Complete!${NC}"
echo -e "${GREEN}📊 Report generated: ${REPORT_FILE}${NC}"

# Show summary
echo -e "\n${BLUE}📋 Quick Summary:${NC}"
if grep -q "🟢 GO" "$REPORT_FILE"; then
    echo -e "${GREEN}✅ AUDIT PASSED - GO FOR LAUNCH${NC}"
    exit 0
else
    echo -e "${RED}❌ AUDIT FAILED - NO-GO FOR LAUNCH${NC}"
    echo -e "${YELLOW}📝 Review the full report for details: ${REPORT_FILE}${NC}"
    exit 1
fi 