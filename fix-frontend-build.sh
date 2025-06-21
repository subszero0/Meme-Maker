#!/bin/bash

echo "🔧 Fixing frontend build issues..."

# Stop containers
echo "Stopping containers..."
docker-compose down

# Remove any existing frontend images to force rebuild
echo "Removing old frontend images..."
docker rmi meme-maker-frontend:latest 2>/dev/null || true
docker rmi $(docker images -q --filter "reference=meme-maker_frontend*") 2>/dev/null || true

# Clean up any build cache
echo "Cleaning build cache..."
docker builder prune -f

# Rebuild and start containers
echo "Rebuilding and starting containers..."
docker-compose up -d --build

echo "✅ Frontend build fixed! Checking container status..."
sleep 15
docker-compose ps
echo ""
echo "📋 Container logs:"
docker-compose logs frontend --tail=20 