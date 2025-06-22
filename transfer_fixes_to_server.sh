#!/bin/bash
# Script to transfer domain and HTTPS fixes to the server
# Run this on your LOCAL machine, then SSH to server

echo "📡 Transferring Domain and HTTPS Fixes to Server"
echo "================================================"

# Check if we're in the right directory
if [ ! -f "docker-compose.yaml" ]; then
    echo "❌ Please run this script from your Meme-Maker directory"
    exit 1
fi

echo "🔍 Checking for required files..."

# List of files that need to be on the server
required_files=(
    "docker-compose.yaml"
    "frontend-new/nginx.conf"
    "deploy_domain_https_fix.sh"
    "setup_ssl_certificate.sh"
    "verify_domain_https_fix.py"
    "DOMAIN_HTTPS_FIX_SUMMARY.md"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file - MISSING"
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo ""
    echo "❌ Missing files detected. Please ensure all files are created first."
    exit 1
fi

echo ""
echo "📋 TRANSFER OPTIONS:"
echo "==================="
echo ""
echo "Option 1: Git Push/Pull (Recommended)"
echo "--------------------------------------"
echo "1. Commit changes locally:"
echo "   git add ."
echo "   git commit -m 'Add domain and HTTPS fixes'"
echo "   git push origin main"
echo ""
echo "2. Pull on server:"
echo "   cd ~/Meme-Maker"
echo "   git pull origin main"
echo ""
echo "Option 2: SCP Transfer"
echo "---------------------"
echo "Replace YOUR_SERVER_IP with your Lightsail IP (13.126.173.223)"
echo "Replace YOUR_KEY_FILE with your SSH key file"
echo ""
echo "scp -i YOUR_KEY_FILE docker-compose.yaml ubuntu@YOUR_SERVER_IP:~/Meme-Maker/"
echo "scp -i YOUR_KEY_FILE frontend-new/nginx.conf ubuntu@YOUR_SERVER_IP:~/Meme-Maker/frontend-new/"
echo "scp -i YOUR_KEY_FILE deploy_domain_https_fix.sh ubuntu@YOUR_SERVER_IP:~/Meme-Maker/"
echo "scp -i YOUR_KEY_FILE setup_ssl_certificate.sh ubuntu@YOUR_SERVER_IP:~/Meme-Maker/"
echo "scp -i YOUR_KEY_FILE verify_domain_https_fix.py ubuntu@YOUR_SERVER_IP:~/Meme-Maker/"
echo "scp -i YOUR_KEY_FILE DOMAIN_HTTPS_FIX_SUMMARY.md ubuntu@YOUR_SERVER_IP:~/Meme-Maker/"
echo ""
echo "Option 3: Manual File Creation"
echo "------------------------------"
echo "If git/scp don't work, you can manually create the files on the server."
echo "See the file contents in DOMAIN_HTTPS_FIX_SUMMARY.md"
echo ""
echo "🎯 RECOMMENDED: Use Option 1 (Git) as it's the most reliable" 