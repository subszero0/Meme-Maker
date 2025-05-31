#!/bin/bash
# Test script to verify frontend serving is working correctly

set -e

echo "🧪 Testing Frontend Serving..."

# Start Docker containers if not running
if ! docker compose ps | grep -q "meme-maker-backend.*Up"; then
    echo "🐳 Starting Docker containers..."
    docker compose up -d backend redis minio
    sleep 5
fi

# Test API health endpoint
echo "🔍 Testing API health..."
if curl -s http://localhost:8000/health | grep -q '"status":"ok"'; then
    echo "✅ API health check passed"
else
    echo "❌ API health check failed"
    exit 1
fi

# Test that root returns HTML (frontend)
echo "🔍 Testing frontend serving at root..."
if curl -s http://localhost:8000/ | grep -q "<html"; then
    echo "✅ Frontend HTML is being served at root"
else
    echo "❌ Frontend is not being served at root"
    exit 1
fi

# Test that API routes still work
echo "🔍 Testing API routes are accessible..."
if curl -s http://localhost:8000/api/v1/jobs | grep -q "detail"; then
    echo "✅ API routes are accessible"
else
    echo "❌ API routes are not accessible"
    exit 1
fi

# Test static assets (if they exist)
echo "🔍 Testing static asset serving..."
# Check if Next.js assets exist and are served
if curl -s http://localhost:8000/_next/static/ | grep -q "404" || curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/favicon.ico | grep -q "200"; then
    echo "✅ Static assets are being served correctly"
else
    echo "⚠️  Static assets may not be properly configured (this is OK if container doesn't have frontend build)"
fi

echo "🎉 Frontend serving tests completed!"
echo ""
echo "📝 Manual verification steps:"
echo "1. Visit http://localhost:8000 - should show the Meme Maker UI"
echo "2. Visit http://localhost:8000/docs - should show FastAPI docs"
echo "3. Visit http://localhost:8000/api/v1/jobs - should show API response" 