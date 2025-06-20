#!/bin/bash

echo "🔧 Fixing storage directory permissions..."

# Stop containers first
echo "Stopping containers..."
docker-compose down

# Ensure storage directory exists with correct permissions
echo "Creating storage directory with correct permissions..."
sudo mkdir -p /opt/meme-maker/storage
sudo chown -R $USER:$USER /opt/meme-maker/storage
sudo chmod -R 755 /opt/meme-maker/storage

# Clean up any existing named volumes
echo "Cleaning up old volumes..."
docker volume rm meme-maker_clips-storage 2>/dev/null || true

# Restart containers
echo "Starting containers..."
docker-compose up -d

echo "✅ Permissions fixed! Checking container status..."
sleep 10
docker-compose ps 