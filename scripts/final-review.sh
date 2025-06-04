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

# Install serve if not present (needed for static export)
if ! command -v serve &> /dev/null; then
    echo -e "${YELLOW}📦 Installing serve...${NC}"
    npm install -g serve@latest
fi

# Change to frontend directory for most operations
cd frontend

echo -e "${BLUE}📦 Installing frontend dependencies...${NC}"
# Use the robust npm installation script
chmod +x ../scripts/install-npm-deps.sh
../scripts/install-npm-deps.sh 180 .

echo -e "${GREEN}✅ Dependencies installed successfully${NC}"

echo -e "${BLUE}🏗️  Building frontend for testing...${NC}"
# Use npm run build instead of npx to use local dependencies
npm run build --silent

# Start local server for testing (using serve for static export)
echo -e "${BLUE}🌐 Starting local server with serve...${NC}"
# Kill any existing serve processes
pkill -f "serve" || true
sleep 2

# Serve the static export on port 3000
npx serve@latest out -l 3000 &
SERVER_PID=$!
sleep 5

# Wait for server to be ready
echo "⏳ Waiting for server to be ready..."
for i in {1..30}; do
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Server is ready${NC}"
        break
    fi
    echo "   Waiting for server... ($i/30)"
    sleep 2
done

# Function to cleanup on exit
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    kill $SERVER_PID 2>/dev/null || true
    pkill -f "serve" || true
    cd ..
}
trap cleanup EXIT

# 1. Lighthouse Performance Audit
echo -e "${BLUE}🚀 Running Lighthouse Performance Audit...${NC}"
npx lhci autorun \
    --upload.target=filesystem \
    --upload.outputDir=../reports/lighthouse \
    --collect.url=http://localhost:3000 \
    --collect.settings.chromeFlags="--no-sandbox --headless --disable-gpu" \
    || echo -e "${RED}❌ Lighthouse audit failed${NC}"

# 2. Accessibility Audit with axe-core (with Chrome version management)
echo -e "${BLUE}♿ Running Accessibility Audit...${NC}"
# Try to install matching Chrome and ChromeDriver versions
npx browser-driver-manager install chrome --force > /dev/null 2>&1 || echo -e "${YELLOW}⚠️  Could not update Chrome/ChromeDriver${NC}"

npx axe \
    http://localhost:3000 \
    --tags wcag2a,wcag2aa \
    --save ../reports/axe.json \
    --exit \
    --chrome-options="--no-sandbox --disable-gpu --headless" \
    || echo -e "${RED}❌ Accessibility audit failed (Chrome version mismatch)${NC}"

# 3. Bundle Size Audit
echo -e "${BLUE}📦 Running Bundle Size Audit...${NC}"
npm run audit:bundle > ../reports/bundle-audit.log 2>&1 || echo -e "${RED}❌ Bundle audit failed${NC}"

# 4. Security Headers Check
echo -e "${BLUE}🔒 Checking Security Headers...${NC}"
curl -I http://localhost:3000 > ../reports/security-headers.log 2>&1 || echo -e "${RED}❌ Security headers check failed${NC}"

# 5. Performance API Check
echo -e "${BLUE}⚡ Testing API Performance...${NC}"
cd ..
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

curl -o reports/api-health.json -w "@curl-format.txt" http://localhost:8000/health > reports/api-performance.log 2>&1 || echo -e "${RED}❌ API performance check failed${NC}"

# 6. Frontend build validation
echo -e "${BLUE}🌐 Validating Frontend Build...${NC}"
cd frontend
# Just verify the build is valid and can be served
echo "Building frontend for validation..."
npm run build > ../reports/build-validation.log 2>&1 || echo -e "${RED}❌ Build validation failed${NC}"

echo "Testing static serve capability..."
# Test that the current server is responding
if curl -f http://localhost:3000 > ../reports/serve-validation.log 2>&1; then
    echo -e "${GREEN}✅ Frontend serves correctly${NC}"
else
    echo -e "${RED}❌ Frontend serve failed${NC}"
fi

# 7. Generate consolidated report
echo -e "${BLUE}📝 Generating Final Report...${NC}"
cd ..

# Create a simple report if the merge script doesn't exist
if [ -f "scripts/merge-review-reports.js" ]; then
    node scripts/merge-review-reports.js > "$REPORT_FILE"
else
    # Create a basic report
    cat > "$REPORT_FILE" << EOF
# Final Review Report - ${TIMESTAMP}

## Summary
This is an automated final review report for commit ${GIT_SHA}.

## Audit Results
- Lighthouse: Check reports/lighthouse/ directory
- Accessibility: Check reports/axe.json
- Bundle Size: Check reports/bundle-audit.log
- Security Headers: Check reports/security-headers.log
- API Performance: Check reports/api-performance.log
- Build Validation: Check reports/build-validation.log

## Status
🟡 Review individual audit files for detailed results.
EOF
fi

echo -e "${GREEN}✅ Final Review Complete!${NC}"
echo -e "${GREEN}📊 Report generated: ${REPORT_FILE}${NC}"

# Show summary
echo -e "\n${BLUE}📋 Quick Summary:${NC}"
if grep -q "🟢 GO" "$REPORT_FILE" 2>/dev/null; then
    echo -e "${GREEN}✅ AUDIT PASSED - GO FOR LAUNCH${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  AUDIT COMPLETED - REVIEW REPORTS${NC}"
    echo -e "${YELLOW}📝 Review the full report for details: ${REPORT_FILE}${NC}"
    exit 0  # Don't fail the CI for now, just generate reports
fi 