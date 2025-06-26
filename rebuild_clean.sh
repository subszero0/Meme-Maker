#!/bin/bash
echo "🔧 Starting clean rebuild of Meme Maker application..."

cd /home/ubuntu/Meme-Maker

# Check Docker Compose is working
echo "📋 Validating Docker Compose configuration..."
docker-compose config > /dev/null
if [ $? -ne 0 ]; then
    echo "❌ Docker Compose configuration has errors!"
    exit 1
fi
echo "✅ Docker Compose configuration is valid"

# Build and start services
echo "🏗️ Building and starting services..."
docker-compose up -d --build

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 10

# Check container status
echo "📊 Checking container status..."
docker-compose ps

# Test endpoints
echo "🔍 Testing endpoints..."
echo "Testing backend health..."

# Check backend health and get logs on failure
if ! curl -s -f http://localhost:8000/health > /dev/null; then
    echo "❌ Backend health check failed. Dumping logs..."
    docker-compose logs --no-color --tail="100" backend
    exit 1
else
    echo "✅ Backend health check passed."
fi

echo "Testing frontend on port 80..."
curl -s -o /dev/null -w "Frontend port 80: %{http_code}\n" http://localhost:80/ || echo "❌ Frontend port 80 failed"

echo "Testing IP access..."
curl -s -o /dev/null -w "IP access: %{http_code}\n" http://13.126.173.223/ || echo "❌ IP access failed"

echo "Testing domain access..."
curl -s -o /dev/null -w "Domain access: %{http_code}\n" http://memeit.pro/ || echo "❌ Domain access failed"

echo "Testing API through nginx..."
curl -s -o /dev/null -w "API through nginx: %{http_code}\n" http://localhost:80/api/health || echo "❌ API through nginx failed"

echo ""
echo "🎯 Rebuild complete! Check the results above."
echo "✅ If all tests show status 200, the application is working correctly."
echo "⚠️  If any tests failed, check the container logs with: docker-compose logs [service-name]" 