#!/bin/bash
set -e

echo "🔧 FIXING DOCKER NETWORK ISSUE..."
echo "================================="

echo "🔍 Checking existing Docker networks..."
docker network ls

echo ""
echo "🏗️  Creating staging network if it doesn't exist..."
docker network create meme-maker-staging_staging-network --driver bridge || {
    echo "✅ Network already exists or created successfully"
}

echo ""
echo "🔍 Verifying network exists..."
docker network ls | grep staging-network

echo ""
echo "🚀 Starting staging deployment..."

# First start the base staging services to create the network properly
echo "Step 1: Starting base staging services..."
docker-compose -f docker-compose.staging.yml up -d

echo "Waiting for base services to start..."
sleep 15

# Then add the monitoring services
echo "Step 2: Adding monitoring services..."
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml --env-file .env.monitoring.staging up -d

echo ""
echo "✅ Deployment completed!"

echo ""
echo "🔍 Checking all container status..."
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml ps

echo ""
echo "📊 Testing services..."

# Test each service
services=(
    "http://localhost:8082/ Application"
    "http://localhost:8001/health Backend"
    "http://localhost:9090/-/healthy Prometheus"
    "http://localhost:3001/api/health Grafana"
)

for service in "${services[@]}"; do
    url=$(echo $service | cut -d' ' -f1)
    name=$(echo $service | cut -d' ' -f2-)
    
    if curl -f -s "$url" >/dev/null 2>&1; then
        echo "✅ $name: HEALTHY"
    else
        echo "❌ $name: NOT RESPONDING"
    fi
done

echo ""
echo "🎉 STAGING DEPLOYMENT COMPLETE!"
echo "================================"
echo ""
echo "📊 Access URLs:"
echo "  Application: http://13.126.173.223:8082/"
echo "  Prometheus:  http://13.126.173.223:9090/"
echo "  Grafana:     http://13.126.173.223:3001/"
echo "    Username: admin"
echo "    Password: staging_admin_2025_secure"
echo ""
echo "🔥 If Prometheus/Grafana not accessible externally:"
echo "    Run: ./scripts/fix_staging_firewall.sh" 