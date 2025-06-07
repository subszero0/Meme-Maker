#!/bin/bash
set -e

echo "🚀 Deploying Meme Maker to VPS..."

# Debug SSH setup
echo "SSH_HOST: $SSH_HOST"
echo "SSH connection test..."

# Check local SSH key fingerprint
echo "📋 Local SSH key fingerprint:"
ssh-keygen -lf ~/.ssh/id_rsa || echo "Could not read local key fingerprint"

# Check which public key is expected on the server
echo "🔍 Checking server's authorized_keys for our public key..."
LOCAL_PUBLIC_KEY=$(ssh-keygen -yf ~/.ssh/id_rsa 2>/dev/null || echo "Could not extract public key")
echo "Our public key: $LOCAL_PUBLIC_KEY"

# Test SSH connection with verbose output
echo "🔐 Testing SSH connection with verbose output..."
if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -v -T $SSH_HOST 'echo "SSH connection successful"' 2>&1; then
  echo "✅ SSH connection test passed"
else
  echo "❌ SSH connection test failed"
  echo "🔍 Attempting to diagnose the issue..."
  
  # Try to see what's in the authorized_keys file (this might fail but worth trying)
  echo "Checking if we can identify the authentication issue..."
  ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o PasswordAuthentication=no -v $SSH_HOST 'exit' 2>&1 | grep -E "(debug1|Offering|userauth_pubkey)" || echo "Could not get detailed SSH debug info"
  
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