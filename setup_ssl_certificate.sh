#!/bin/bash
# SSL Certificate Setup Script for memeit.pro
# This script sets up SSL certificates using Let's Encrypt

set -e

echo "🔐 Setting up SSL Certificate for memeit.pro"
echo "=============================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Install certbot if not already installed
echo "📦 Installing certbot..."
if ! command -v certbot &> /dev/null; then
    apt update
    apt install -y snapd
    snap install core
    snap refresh core
    snap install --classic certbot
    ln -sf /snap/bin/certbot /usr/bin/certbot
else
    echo "✅ Certbot already installed"
fi

# Stop nginx temporarily to allow certbot to bind to port 80
echo "⏸️  Stopping nginx temporarily..."
docker-compose down frontend || true

# Get SSL certificate
echo "🔒 Obtaining SSL certificate..."
certbot certonly \
    --standalone \
    --email admin@memeit.pro \
    --agree-tos \
    --non-interactive \
    --domains memeit.pro,www.memeit.pro

# Create SSL directory in the project
echo "📁 Setting up SSL directories..."
mkdir -p ssl/certs
mkdir -p ssl/private

# Copy certificates to project directory
echo "📋 Copying certificates..."
cp /etc/letsencrypt/live/memeit.pro/fullchain.pem ssl/certs/memeit.pro.crt
cp /etc/letsencrypt/live/memeit.pro/privkey.pem ssl/private/memeit.pro.key

# Set proper permissions
chmod 644 ssl/certs/memeit.pro.crt
chmod 600 ssl/private/memeit.pro.key

echo "✅ SSL certificates installed successfully!"
echo ""
echo "📋 Certificate Information:"
echo "   Certificate: ssl/certs/memeit.pro.crt"
echo "   Private Key: ssl/private/memeit.pro.key"
echo "   Expires: $(openssl x509 -enddate -noout -in ssl/certs/memeit.pro.crt)"
echo ""
echo "🔄 Next steps:"
echo "1. Update docker-compose.yaml to mount SSL certificates"
echo "2. Restart the application with: docker-compose up -d"
echo "3. Test HTTPS access: https://memeit.pro"
echo ""
echo "⏰ Set up automatic renewal:"
echo "   Add to crontab: 0 12 * * * /usr/bin/certbot renew --quiet" 