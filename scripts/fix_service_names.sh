#!/bin/bash
echo "🔧 FIXING SERVICE NAME MISMATCH..."
echo "=================================="

# This fixes the issue where monitoring compose file was looking for 'backend' and 'redis'
# but staging compose file has 'backend-staging' and 'redis-staging'

echo "✅ Service name mismatch fixed in latest commit"
echo "✅ Now pulling latest fixes..."

# Pull the latest fix
git pull origin monitoring-staging

echo ""
echo "🎯 Now restart the deployment:"
echo "1. docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml --env-file .env.monitoring.staging down --remove-orphans"
echo "2. docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml --env-file .env.monitoring.staging up -d"

echo ""
echo "📊 Then test:"
echo "- Application: http://localhost:8082/"
echo "- Backend: http://localhost:8001/health" 
echo "- Prometheus: http://localhost:9090/-/healthy"
echo "- Grafana: http://localhost:3001/api/health" 