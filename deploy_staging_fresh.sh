#!/bin/bash
set -e

echo "🚀 Deploying Fresh Staging Environment..."

# 1. Verify environment file exists
if [ ! -f ".env.monitoring.staging" ]; then
    echo "❌ Environment file missing. Run ./create_staging_env.sh first"
    exit 1
fi

# 2. Deploy core services first (without monitoring)
echo "🔧 Deploying core services..."
docker-compose -f docker-compose.staging.yml up -d

# 3. Wait for core services to initialize
echo "⏳ Waiting for core services to initialize..."
sleep 30

# 4. Verify core services are running
echo "✅ Checking core services..."
docker-compose -f docker-compose.staging.yml ps

# 5. Deploy monitoring stack
echo "📊 Deploying monitoring stack..."
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml --env-file .env.monitoring.staging up -d

# 6. Wait for monitoring services to initialize
echo "⏳ Waiting for monitoring services to initialize..."
sleep 60

# 7. Final verification
echo "🔍 Final verification..."
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml ps

echo ""
echo "✅ Fresh staging deployment completed!"
echo ""
echo "🎯 Service URLs:"
echo "  Application: http://13.126.173.223:8082/"
echo "  Backend API: http://13.126.173.223:8001/health"
echo "  Prometheus: http://13.126.173.223:9090/"
echo "  Grafana: http://13.126.173.223:3001/ (admin / staging_admin_2025_secure)"
echo ""
echo "🔄 Test the application and then retry GitHub CI/CD" 