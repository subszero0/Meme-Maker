#!/bin/bash
set -e

echo "🚨 Fixing Docker Container Metadata Corruption..."
echo "⚠️  This will clean ALL Docker state and rebuild from scratch"

# 1. Stop and remove ALL containers (corrupted and clean)
echo "🛑 Stopping all containers..."
docker-compose -f docker-compose.staging.yml down --remove-orphans 2>/dev/null || true
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml down --remove-orphans 2>/dev/null || true

# 2. Force remove any stuck containers
echo "🗑️  Force removing any remaining containers..."
docker ps -aq | xargs -r docker stop 2>/dev/null || true
docker ps -aq | xargs -r docker rm -f 2>/dev/null || true

# 3. Clean corrupted Docker state (AGGRESSIVE CLEANUP)
echo "🧹 Cleaning Docker system state..."
docker system prune -af --volumes 2>/dev/null || true
docker network prune -f 2>/dev/null || true
docker volume prune -f 2>/dev/null || true

# 4. Remove potentially corrupted images
echo "🔄 Removing potentially corrupted images..."
docker images | grep -E "(redis|meme-maker)" | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true

# 5. Clean Docker cache and metadata
echo "🗂️  Cleaning Docker cache..."
docker builder prune -af 2>/dev/null || true

# 6. Restart Docker daemon to clear memory state
echo "🔄 Restarting Docker daemon..."
sudo systemctl restart docker
sleep 10

echo "✅ Docker cleanup completed!"
echo "🔧 Ready for fresh deployment" 