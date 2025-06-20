#!/bin/bash
# Production Setup Script for Meme Maker on Lightsail
# Run this script on your Lightsail instance after cloning the repository

set -e

echo "🚀 Setting up Meme Maker for production deployment..."

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Please don't run this script as root. Run as ubuntu user."
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker if not installed
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✅ Docker installed. You'll need to logout and login again for group changes to take effect."
else
    echo "✅ Docker already installed"
fi

# Install Docker Compose if not installed
if ! command -v docker-compose &> /dev/null; then
    echo "🔧 Installing Docker Compose..."
    sudo apt install docker-compose -y
else
    echo "✅ Docker Compose already installed"
fi

# Install other required packages
echo "📦 Installing additional packages..."
sudo apt install -y git curl nginx htop

# Create storage directory
echo "📁 Creating storage directory..."
sudo mkdir -p /opt/meme-maker/storage
sudo chown $USER:$USER /opt/meme-maker/storage
sudo chmod 755 /opt/meme-maker/storage

# Check if .env exists, if not create from template
if [ ! -f .env ]; then
    echo "⚙️  Creating .env file from template..."
    cp env.template .env
    echo "📝 Please edit .env file with your production settings before continuing!"
    echo "   nano .env"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🎉 Production setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file: nano .env"
echo "2. Update BASE_URL and CORS_ORIGINS with your domain/IP"
echo "3. If you need to logout/login for Docker group: exit, then ssh back in"
echo "4. Run: docker-compose up -d"
echo ""
echo "Optional (for domain setup):"
echo "5. Configure Nginx reverse proxy"
echo "6. Set up SSL with certbot" 