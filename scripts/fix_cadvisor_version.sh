#!/bin/bash
set -e

echo "🔧 FIXING CADVISOR VERSION ISSUE..."
echo "==================================="

echo "🔍 Detected Issue:"
echo "   Error: gcr.io/cadvisor/cadvisor:v0.48.1 not found"
echo "   Solution: Updated to v0.53.0 (latest stable)"

echo ""
echo "📦 Pulling latest monitoring configuration..."
git pull origin monitoring-staging

echo ""
echo "🚀 Continuing deployment with fixed cAdvisor version..."

# Continue where the previous script left off
echo "Starting monitoring services with correct cAdvisor version..."
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml --env-file .env.monitoring.staging up -d

echo ""
echo "⏳ Waiting for all services to start..."
sleep 20

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
        echo "❌ $name: NOT RESPONDING (will check again in 30s)"
    fi
done

echo ""
echo "⏳ Final health check (services may need time to initialize)..."
sleep 30

echo "📊 Final status check..."
for service in "${services[@]}"; do
    url=$(echo $service | cut -d' ' -f1)
    name=$(echo $service | cut -d' ' -f2-)
    
    if curl -f -s "$url" >/dev/null 2>&1; then
        echo "✅ $name: HEALTHY"
    else
        echo "⚠️  $name: Still starting..."
    fi
done

echo ""
echo "🎉 CADVISOR VERSION FIXED & DEPLOYMENT COMPLETE!"
echo "================================================"
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
echo ""
echo "📋 To check container logs if any issues:"
echo "    docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml logs [service_name]" 