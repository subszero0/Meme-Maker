#!/bin/bash
set -e

echo "🚀 Deploying Meme Maker to VPS..."

# Debug SSH setup
echo "SSH_HOST: $SSH_HOST"
echo "SSH connection test..."

# Test SSH connection first
if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -T $SSH_HOST 'echo "SSH connection successful"'; then
  echo "✅ SSH connection test passed"
else
  echo "❌ SSH connection test failed"
  exit 1
fi

ssh -o StrictHostKeyChecking=no -T $SSH_HOST <<'EOSSH'
  cd ~/Meme-Maker
  
  echo "📥 Pulling latest code..."
  git pull
  
  echo "🔧 Copying Caddyfile to /etc/caddy/..."
  sudo cp Caddyfile /etc/caddy/Caddyfile
  
  echo "🐳 Building and starting Docker containers..."
  docker compose build
  docker compose up -d
  
  echo "🌐 Restarting Caddy..."
  sudo systemctl restart caddy
  
  echo "⏳ Waiting for services to start..."
  sleep 10
  
  echo "🔍 Checking service health..."
  
  # Check if FastAPI is running
  if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ FastAPI backend is healthy"
  else
    echo "❌ FastAPI backend health check failed"
    exit 1
  fi
  
  # Check if Caddy is serving the site
  if curl -s -H "Host: memeit.pro" http://localhost/ > /dev/null; then
    echo "✅ Caddy is serving requests"
  else
    echo "❌ Caddy health check failed"
    exit 1
  fi
  
  echo "🎉 Deployment successful!"
  echo "Frontend: https://memeit.pro"
  echo "API Docs: https://memeit.pro/docs"
  echo "Health: https://memeit.pro/health"
EOSSH

echo "✅ Deployment completed successfully!" 