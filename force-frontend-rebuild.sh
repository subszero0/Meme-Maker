#!/bin/bash

echo "🚨 Force rebuilding frontend without cache..."

# Stop all containers
echo "Stopping all containers..."
docker-compose down

# Remove ALL images and build cache related to the project
echo "Removing all project images and cache..."
docker rmi $(docker images -q "meme-maker*") 2>/dev/null || true
docker rmi $(docker images -q --filter "reference=*meme-maker*") 2>/dev/null || true
docker system prune -a -f
docker builder prune -a -f

# Remove any dangling images
echo "Cleaning up dangling images..."
docker image prune -f

# Force rebuild from scratch with no cache
echo "Rebuilding frontend from scratch..."
docker-compose build --no-cache --pull frontend

# Start just the frontend to test
echo "Testing frontend build..."
docker-compose up -d redis
sleep 5
docker-compose up -d frontend

echo "✅ Frontend rebuild complete! Checking status..."
sleep 10
docker-compose ps
echo ""
echo "📋 Frontend logs:"
docker-compose logs frontend --tail=30 