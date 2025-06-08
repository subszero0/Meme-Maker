#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📦 Robust npm dependency installation${NC}"

# Set environment variables for optimal npm behavior
export PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
export PUPPETEER_SKIP_DOWNLOAD=true
export NODE_ENV=development
export NPM_CONFIG_AUDIT=false
export NPM_CONFIG_FUND=false
export NPM_CONFIG_SILENT=true
export NPM_CONFIG_PROGRESS=false
export NPM_CONFIG_CACHE=$(pwd)/.npm-cache
# Prevent Cypress from opening GUI during installation
export CI=true

# Configuration
TIMEOUT=${1:-180}  # Default 3 minutes, can be overridden
WORKING_DIR=${2:-frontend}  # Default to frontend directory

echo -e "${BLUE}Working directory: ${WORKING_DIR}${NC}"
echo -e "${BLUE}Timeout: ${TIMEOUT} seconds${NC}"

# Navigate to working directory
cd "$WORKING_DIR"

# Create npm cache directory
echo -e "${BLUE}🔧 Setting up npm cache...${NC}"
mkdir -p .npm-cache

# Function to verify installation
verify_installation() {
    echo -e "${BLUE}🔍 Verifying installation...${NC}"
    if [ -d "node_modules" ] && [ -f "package.json" ]; then
        echo -e "${GREEN}✅ node_modules directory exists${NC}"
        
        # Count installed packages
        PACKAGE_COUNT=$(ls node_modules | wc -l)
        echo -e "${GREEN}📊 Installed packages: ${PACKAGE_COUNT}${NC}"
        
        # Check for critical packages
        CRITICAL_PACKAGES=("next" "react" "react-dom")
        for pkg in "${CRITICAL_PACKAGES[@]}"; do
            if [ -d "node_modules/$pkg" ]; then
                echo -e "${GREEN}✅ $pkg installed${NC}"
            else
                echo -e "${YELLOW}⚠️  $pkg missing${NC}"
            fi
        done
        
        return 0
    else
        echo -e "${RED}❌ Installation verification failed${NC}"
        return 1
    fi
}

# Method 1: Try npm ci (fastest when package-lock.json is valid)
echo -e "${BLUE}🚀 Attempting npm ci...${NC}"
if timeout "$TIMEOUT" npm ci \
    --production=false \
    --legacy-peer-deps \
    --no-audit \
    --no-fund \
    --silent \
    --prefer-offline \
    --cache .npm-cache \
    --maxsockets 1; then
    
    echo -e "${GREEN}✅ npm ci succeeded${NC}"
    verify_installation && exit 0
fi

# Method 2: Clean and try npm install
echo -e "${YELLOW}⚠️  npm ci failed, trying npm install...${NC}"
rm -rf node_modules package-lock.json .npm-cache
mkdir -p .npm-cache

if timeout "$TIMEOUT" npm install \
    --production=false \
    --legacy-peer-deps \
    --no-audit \
    --no-fund \
    --silent \
    --prefer-offline \
    --cache .npm-cache \
    --maxsockets 1; then
    
    echo -e "${GREEN}✅ npm install succeeded${NC}"
    verify_installation && exit 0
fi

# Method 3: Install only essential packages (last resort)
echo -e "${RED}❌ Standard npm install failed, trying minimal essential dependencies...${NC}"

# Install core dependencies first
CORE_DEPS=(
    "next"
    "react"
    "react-dom"
    "typescript"
    "@types/node"
    "@types/react"
    "@types/react-dom"
)

echo -e "${BLUE}Installing core dependencies: ${CORE_DEPS[*]}${NC}"
if npm install --production=false --legacy-peer-deps --no-audit --no-fund --silent "${CORE_DEPS[@]}"; then
    echo -e "${GREEN}✅ Core dependencies installed${NC}"
    
    # Install styling dependencies
    STYLE_DEPS=(
        "tailwindcss"
        "@tailwindcss/postcss"
        "autoprefixer"
    )
    
    echo -e "${BLUE}Installing styling dependencies: ${STYLE_DEPS[*]}${NC}"
    npm install --production=false --legacy-peer-deps --no-audit --no-fund --silent "${STYLE_DEPS[@]}" || {
        echo -e "${YELLOW}⚠️  Some styling dependencies failed to install${NC}"
    }
    
    verify_installation && exit 0
fi

# If all methods fail
echo -e "${RED}❌ All installation methods failed${NC}"
echo -e "${RED}💡 Troubleshooting tips:${NC}"
echo -e "${RED}   - Check internet connectivity${NC}"
echo -e "${RED}   - Verify package.json syntax${NC}"
echo -e "${RED}   - Check for Node.js version compatibility${NC}"
echo -e "${RED}   - Try running locally: cd $WORKING_DIR && npm install${NC}"

exit 1 