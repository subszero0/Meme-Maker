#!/bin/bash
# Transfer HTTPS Setup Scripts to Server
# Run this from your local machine to upload the scripts to your server

set -e

# Configuration
SERVER_USER="ubuntu"
SERVER_IP="13.126.173.223"
SERVER_PATH="/home/ubuntu/Meme-Maker"
KEY_FILE="your-key.pem"  # Update this to your actual key file path

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 HTTPS Setup Scripts Transfer${NC}"
echo "=================================="

# Check if key file exists (if specified)
if [[ "$KEY_FILE" != "your-key.pem" && ! -f "$KEY_FILE" ]]; then
    echo -e "${RED}❌ Key file not found: $KEY_FILE${NC}"
    echo "Please update the KEY_FILE variable in this script"
    exit 1
fi

# Files to transfer
HTTPS_FILES=(
    "stage1_pre_https_verification.py"
    "stage2_ssl_installation.py"
    "stage3_https_deployment.py"
    "verify_https_complete.py"
    "complete_https_setup.py"
    "HTTPS_SETUP_INSTRUCTIONS.md"
)

echo -e "${YELLOW}📋 Files to transfer:${NC}"
for file in "${HTTPS_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo -e "  ✅ $file"
    else
        echo -e "  ❌ $file (missing)"
        exit 1
    fi
done

echo ""
echo -e "${BLUE}🔗 Connecting to server...${NC}"

# Build SCP command
if [[ "$KEY_FILE" == "your-key.pem" ]]; then
    # No key file specified, use default SSH
    SCP_CMD="scp"
    SSH_CMD="ssh"
else
    # Use specified key file
    SCP_CMD="scp -i $KEY_FILE"
    SSH_CMD="ssh -i $KEY_FILE"
fi

# Transfer files
echo -e "${YELLOW}📤 Transferring HTTPS setup scripts...${NC}"
for file in "${HTTPS_FILES[@]}"; do
    echo -n "  Uploading $file... "
    if $SCP_CMD "$file" "${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/"; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC}"
        exit 1
    fi
done

# Make scripts executable on server
echo -e "${YELLOW}🔧 Making scripts executable...${NC}"
$SSH_CMD "${SERVER_USER}@${SERVER_IP}" "cd ${SERVER_PATH} && chmod +x *.py"

# Verify files on server
echo -e "${YELLOW}🔍 Verifying files on server...${NC}"
$SSH_CMD "${SERVER_USER}@${SERVER_IP}" "cd ${SERVER_PATH} && ls -la stage*.py complete_https_setup.py verify_https_complete.py"

echo ""
echo -e "${GREEN}✅ Transfer completed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "1. SSH into your server:"
if [[ "$KEY_FILE" == "your-key.pem" ]]; then
    echo "   ssh ${SERVER_USER}@${SERVER_IP}"
else
    echo "   ssh -i $KEY_FILE ${SERVER_USER}@${SERVER_IP}"
fi
echo ""
echo "2. Navigate to project directory:"
echo "   cd ${SERVER_PATH}"
echo ""
echo "3. Run the complete HTTPS setup:"
echo "   python complete_https_setup.py"
echo ""
echo "   OR run individual stages:"
echo "   python stage1_pre_https_verification.py"
echo "   python stage2_ssl_installation.py"
echo "   python stage3_https_deployment.py"
echo "   python verify_https_complete.py"
echo ""
echo -e "${GREEN}🎯 Goal: Get your application working at https://memeit.pro${NC}"
echo "" 