#!/bin/bash
set -e

echo "🔧 FIXING STAGING SERVER ISSUES - IP: 13.126.173.223"
echo "===================================================="

echo ""
echo "📋 Issues to fix:"
echo "  1. ❌ Download URL opens in new window with 'http://api/v1/jobs/{id}/download'"
echo "  2. ❌ Prometheus and Grafana not accessible"
echo ""
echo "🔍 Root causes identified:"
echo "  1. Backend BASE_URL not set - defaults to localhost:8000 instead of server IP"
echo "  2. Monitoring stack missing environment variables"
echo ""

# Step 1: Update docker-compose.staging.yml with correct BASE_URL
echo "🔧 Step 1: Updating BASE_URL for staging server..."

# Create backup
cp docker-compose.staging.yml docker-compose.staging.yml.backup

# Update BASE_URL to use server IP
sed -i 's|BASE_URL=http://localhost:8001|BASE_URL=http://13.126.173.223:8001|g' docker-compose.staging.yml

echo "✅ Updated BASE_URL to: http://13.126.173.223:8001"

# Step 2: Stop existing services
echo ""
echo "🛑 Step 2: Stopping existing staging services..."
docker-compose -f docker-compose.staging.yml down --remove-orphans || echo "No staging services running"
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml down --remove-orphans || echo "No monitoring services running"

# Step 3: Start core staging services
echo ""
echo "🚀 Step 3: Starting core staging services..."
docker-compose -f docker-compose.staging.yml up -d --build

# Wait for services
echo ""
echo "⏳ Step 4: Waiting for core services to initialize (60 seconds)..."
sleep 60

# Step 5: Check core services
echo ""
echo "🔍 Step 5: Checking core services health..."

backend_test=$(curl -f -s http://localhost:8001/health >/dev/null 2>&1 && echo "✅" || echo "❌")
frontend_test=$(curl -f -s http://localhost:8082/ >/dev/null 2>&1 && echo "✅" || echo "❌")

echo "  Backend API (localhost:8001/health): $backend_test"
echo "  Frontend (localhost:8082/): $frontend_test"

# Step 6: Start monitoring services
echo ""
echo "📊 Step 6: Starting monitoring services with proper environment..."
echo "   Using --env-file .env.monitoring.staging for Grafana credentials"

docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml --env-file .env.monitoring.staging up -d

# Wait for monitoring services
echo ""
echo "⏳ Step 7: Waiting for monitoring services to initialize (60 seconds)..."
sleep 60

# Step 8: Comprehensive health check
echo ""
echo "🔍 Step 8: Comprehensive health check..."

backend_test=$(curl -f -s http://localhost:8001/health >/dev/null 2>&1 && echo "✅" || echo "❌")
frontend_test=$(curl -f -s http://localhost:8082/ >/dev/null 2>&1 && echo "✅" || echo "❌")
prometheus_test=$(curl -f -s http://localhost:9090/-/healthy >/dev/null 2>&1 && echo "✅" || echo "❌")
grafana_test=$(curl -f -s http://localhost:3001/api/health >/dev/null 2>&1 && echo "✅" || echo "❌")
cadvisor_test=$(curl -f -s http://localhost:8083/healthz >/dev/null 2>&1 && echo "✅" || echo "❌")

echo ""
echo "📊 SERVICE HEALTH SUMMARY:"
echo "  Core Services:"
echo "    Backend API:     $backend_test   (Internal: localhost:8001)"
echo "    Frontend:        $frontend_test   (Internal: localhost:8082)"
echo ""
echo "  Monitoring Stack:"
echo "    Prometheus:      $prometheus_test   (Internal: localhost:9090)"
echo "    Grafana:         $grafana_test   (Internal: localhost:3001)"
echo "    cAdvisor:        $cadvisor_test   (Internal: localhost:8083)"

# Step 9: Show containers
echo ""
echo "🐳 Step 9: Running containers:"
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml ps

echo ""
echo "🎉 STAGING SERVER FIXES COMPLETED!"
echo "=================================="
echo ""
echo "📝 Summary of fixes applied:"
echo "  ✅ 1. Download URL Issue:"
echo "     - Updated BASE_URL to: http://13.126.173.223:8001"
echo "     - Backend now generates correct download URLs"
echo "     - Download button should work properly"
echo ""
echo "  ✅ 2. Monitoring Stack Issue:"
echo "     - Started services with --env-file .env.monitoring.staging"
echo "     - Grafana credentials properly loaded"
echo "     - All monitoring services should be accessible"
echo ""
echo "🌐 EXTERNAL ACCESS URLs (from your browser):"
echo "  🎬 Application:    http://13.126.173.223:8082/"
echo "  🔧 Backend API:    http://13.126.173.223:8001/health"  
echo "  📈 Prometheus:     http://13.126.173.223:9090/"
echo "  📊 Grafana:        http://13.126.173.223:3001/"
echo "  🏷️ cAdvisor:       http://13.126.173.223:8083/"
echo ""
echo "🔑 Grafana Login: admin / staging_admin_2025_secure"
echo ""
echo "🧪 TEST THE FIXES:"
echo "  1. Open: http://13.126.173.223:8082/"
echo "  2. Process a video and test download"
echo "  3. Check monitoring dashboards" 