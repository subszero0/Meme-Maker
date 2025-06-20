#!/bin/bash
# Deployment Script for Meme Maker
# Run this after production-setup.sh and configuring .env

set -e

echo "🚀 Deploying Meme Maker..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found! Please create it from env.template first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f docker-compose.yaml ]; then
    echo "❌ docker-compose.yaml not found! Please run from the project root."
    exit 1
fi

# Pull latest changes if this is an update
if [ -d .git ]; then
    echo "📥 Pulling latest changes..."
    git pull origin main || echo "⚠️  Could not pull latest changes (maybe no internet or not a git repo)"
fi

# Create storage directory if it doesn't exist
echo "📁 Ensuring storage directory exists..."
sudo mkdir -p /opt/meme-maker/storage
sudo chown $USER:$USER /opt/meme-maker/storage

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down || echo "No containers to stop"

# Build and start containers
echo "🔨 Building and starting containers..."
docker-compose build --no-cache
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check container status
echo "📊 Container status:"
docker-compose ps

# Test health endpoint
echo "🏥 Testing health endpoint..."
if curl -f http://localhost:8000/health &> /dev/null; then
    echo "✅ Backend health check passed!"
else
    echo "⚠️  Backend health check failed. Check logs with: docker-compose logs backend"
fi

# Test frontend
echo "🌐 Testing frontend..."
if curl -f http://localhost:80/ &> /dev/null; then
    echo "✅ Frontend is responding!"
else
    echo "⚠️  Frontend not responding. Check logs with: docker-compose logs frontend"
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "1. Check all services: docker-compose ps"
echo "2. View logs: docker-compose logs -f"
echo "3. Test in browser: http://your-lightsail-ip"
echo ""
echo "🔧 Optional configuration:"
echo "- Set up Nginx reverse proxy for domain access"
echo "- Configure SSL with certbot"
echo "- Set up monitoring and alerts" 