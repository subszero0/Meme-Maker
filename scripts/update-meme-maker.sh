#!/bin/bash
# Update script for Meme Maker in production
# Run this to pull latest changes and restart the application

set -e

echo "🔄 Updating Meme Maker..."

# Navigate to the project directory
cd ~/Meme-Maker || cd /home/ubuntu/Meme-Maker || {
    echo "❌ Could not find Meme-Maker directory"
    exit 1
}

# Pull latest changes
echo "📥 Pulling latest changes from GitHub..."
git pull origin main

# Stop containers
echo "🛑 Stopping containers..."
docker-compose down

# Rebuild and restart containers
echo "🔨 Rebuilding containers..."
docker-compose build --no-cache

echo "▶️  Starting containers..."
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 30

# Show status
echo "📊 Container status:"
docker-compose ps

# Test health
echo "🏥 Testing application health..."
if curl -f http://localhost:8000/health &> /dev/null; then
    echo "✅ Backend is healthy!"
else
    echo "⚠️  Backend health check failed"
fi

if curl -f http://localhost:80/ &> /dev/null; then
    echo "✅ Frontend is responding!"
else
    echo "⚠️  Frontend not responding"
fi

echo ""
echo "✅ Meme Maker updated successfully!"
echo "📝 Check logs with: docker-compose logs -f" 