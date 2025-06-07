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
  # Stash any local changes to avoid merge conflicts
  git stash push -m "Auto-stash during deployment $(date)" || echo "Nothing to stash"
  
  # Force reset to ensure we get the latest version
  echo "🔄 Ensuring clean state..."
  git fetch origin main
  git reset --hard origin/main
  
  echo "✅ Repository updated to latest version"
  
  echo "🔧 Copying Caddyfile to /etc/caddy/..."
  sudo cp Caddyfile /etc/caddy/Caddyfile
  
  echo "🐳 Building and starting Docker containers..."
  docker compose build
  docker compose up -d
  
  echo "🌐 Restarting Caddy..."
  sudo systemctl restart caddy
  
  echo "⏳ Waiting for services to start..."
  sleep 15
  
  echo "🔄 Giving backend extra time to initialize..."
  sleep 5
  
  echo "🔍 Checking service health..."
  
  # Check Docker container status first
  echo "📊 Docker container status:"
  docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
  
  # Check backend container logs for any startup errors
  echo "📋 Backend container logs (last 10 lines):"
  docker logs meme-maker-backend --tail 10 || echo "Could not fetch backend logs"
  
  # Check if FastAPI is running with more detailed diagnostics
  echo "🔍 Testing FastAPI health endpoint..."
  if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ FastAPI backend is healthy"
  else
    echo "❌ FastAPI backend health check failed"
    echo "🔍 Debugging backend connectivity..."
    
    # Check if port 8000 is listening
    echo "📡 Checking if port 8000 is listening:"
    netstat -tlnp | grep :8000 || echo "Port 8000 not found in netstat"
    
    # Try to get more details from curl
    echo "🌐 Detailed curl response:"
    curl -v http://localhost:8000/health 2>&1 || echo "Curl failed"
    
    # Check if backend container is actually running
    echo "🐳 Backend container status:"
    docker ps | grep meme-maker-backend || echo "Backend container not found in ps"
    
    # Get more backend logs
    echo "📜 Full backend container logs:"
    docker logs meme-maker-backend || echo "Could not fetch full backend logs"
    
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
  
  echo ""
  echo "🔧 Running service diagnostics..."
  chmod +x scripts/debug_vps_services.sh
  ./scripts/debug_vps_services.sh
  
  echo ""
  echo "🔬 Running targeted SSL & Backend diagnostics..."
  chmod +x scripts/diagnose_ssl_backend.sh
  ./scripts/diagnose_ssl_backend.sh
EOSSH

echo "✅ Deployment completed successfully!" 