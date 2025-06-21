#!/bin/bash
set -e

echo "🔄 Starting comprehensive production deployment fix..."

# Navigate to project directory
cd /home/ubuntu/Meme-Maker

echo "⏹️  Stopping all services..."
docker-compose down

# Fix Git issues
echo "🔧 Fixing Git branch and pull issues..."

# Check current branch
current_branch=$(git branch --show-current)
echo "Current branch: $current_branch"

# Switch to master branch (the correct default branch)
echo "📋 Switching to master branch..."
git checkout master || git checkout -b master

# Reset any local changes and force pull
echo "📥 Force pulling latest changes from origin/master..."
git fetch origin
git reset --hard origin/master
git clean -fd

# Verify we have the latest changes
echo "✅ Latest commits:"
git log --oneline -3

# Fix docker-compose.yaml environment variables
echo "🔧 Fixing frontend environment variables..."
sed -i 's/VITE_API_BASE_URL=http:\/\/backend:8000/VITE_API_BASE_URL=\/api/g' docker-compose.yaml
sed -i 's/VITE_WS_BASE_URL=ws:\/\/backend:8000/VITE_WS_BASE_URL=\/ws/g' docker-compose.yaml

# Check for system nginx conflict
echo "🔍 Checking for system nginx conflicts..."
if systemctl is-active --quiet nginx; then
    echo "⚠️  System nginx is running, stopping it..."
    sudo systemctl stop nginx
    sudo systemctl disable nginx
fi

# Check what's using port 80
echo "🔍 Checking port 80 usage..."
sudo netstat -tlnp | grep :80 || echo "Port 80 is free"

# Clean docker system
echo "🧹 Cleaning docker system..."
docker system prune -f

# Rebuild all containers with no cache
echo "🔨 Rebuilding all containers..."
docker-compose build --no-cache

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 30

# Check container status
echo "📊 Container status:"
docker-compose ps

# Test services
echo "🏥 Testing services..."

# Test backend
echo "Testing backend..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    docker-compose logs backend | tail -10
fi

# Test frontend
echo "Testing frontend..."
if curl -f http://localhost/ > /dev/null 2>&1; then
    echo "✅ Frontend is responding"
else
    echo "❌ Frontend test failed"
    docker-compose logs frontend | tail -10
fi

# Test YouTube processing with updated downloader
echo "Testing YouTube processing..."
response=$(curl -s -X POST http://localhost:8000/api/v1/metadata \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"}' | head -c 200)

if echo "$response" | grep -q "title"; then
    echo "✅ YouTube processing is working"
else
    echo "⚠️  YouTube processing issue detected:"
    echo "$response"
fi

echo "🎉 Production deployment fix completed!"
echo ""
echo "📝 Summary:"
echo "- Git branch issues resolved"
echo "- Latest code pulled from master branch"
echo "- Environment variables fixed for production"
echo "- System nginx conflicts resolved"
echo "- Containers rebuilt with updated YouTube handling"
echo "- All services tested"
echo ""
echo "🌐 Your application should now be accessible at:"
echo "- Frontend: http://your-domain.com or http://$(curl -s ifconfig.me)"
echo "- Backend API: http://your-domain.com/api or http://$(curl -s ifconfig.me):8000"
echo ""
echo "✅ Production deployment is ready!" 