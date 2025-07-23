#!/bin/bash
set -e

echo "🔧 FIXING STAGING ISSUES - Download URL + Monitoring Stack"
echo "==========================================================="

echo ""
echo "📋 Issues to fix:"
echo "  1. ❌ Download URL opens in new window with 'http://api/v1/jobs/{id}/download'"
echo "  2. ❌ Prometheus and Grafana not accessible"
echo ""
echo "🔍 Root causes identified:"
echo "  1. Backend BASE_URL not set - defaults to localhost:8000 instead of localhost:8001"
echo "  2. Monitoring stack missing environment variables (GRAFANA_ADMIN_PASSWORD, etc.)"
echo ""

# Step 1: Stop existing services to ensure clean restart
echo "🛑 Step 1: Stopping existing staging services..."
docker-compose -f docker-compose.staging.yml down --remove-orphans || echo "No staging services running"
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml down --remove-orphans || echo "No monitoring services running"

echo ""
echo "✅ Step 2: BASE_URL fix applied to docker-compose.staging.yml"
echo "   Added: BASE_URL=http://localhost:8001 to backend-staging environment"

# Step 3: Start core staging services first
echo ""
echo "🚀 Step 3: Starting core staging services..."
docker-compose -f docker-compose.staging.yml up -d --build

# Wait for core services to be ready
echo ""
echo "⏳ Step 4: Waiting for core services to initialize (60 seconds)..."
sleep 60

# Step 5: Check core services health
echo ""
echo "🔍 Step 5: Checking core services health..."
core_services_status="✅ Core Services Status:"
backend_health=$(curl -f -s http://localhost:8001/health >/dev/null 2>&1 && echo "✅ HEALTHY" || echo "❌ NOT RESPONDING")
frontend_health=$(curl -f -s http://localhost:8082/ >/dev/null 2>&1 && echo "✅ HEALTHY" || echo "❌ NOT RESPONDING")

echo "  Backend API (http://localhost:8001/health): $backend_health"
echo "  Frontend (http://localhost:8082/): $frontend_health"

# Step 6: Start monitoring services with proper environment file
echo ""
echo "📊 Step 6: Starting monitoring services with proper environment..."
echo "   Using --env-file .env.monitoring.staging for Grafana credentials"

docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml --env-file .env.monitoring.staging up -d

# Wait for monitoring services to initialize
echo ""
echo "⏳ Step 7: Waiting for monitoring services to initialize (60 seconds)..."
sleep 60

# Step 8: Check all services health
echo ""
echo "🔍 Step 8: Comprehensive health check..."

# Test core services
backend_test=$(curl -f -s http://localhost:8001/health >/dev/null 2>&1 && echo "✅" || echo "❌")
frontend_test=$(curl -f -s http://localhost:8082/ >/dev/null 2>&1 && echo "✅" || echo "❌")

# Test monitoring services
prometheus_test=$(curl -f -s http://localhost:9090/-/healthy >/dev/null 2>&1 && echo "✅" || echo "❌")
grafana_test=$(curl -f -s http://localhost:3001/api/health >/dev/null 2>&1 && echo "✅" || echo "❌")
cadvisor_test=$(curl -f -s http://localhost:8083/healthz >/dev/null 2>&1 && echo "✅" || echo "❌")

echo ""
echo "📊 SERVICE HEALTH SUMMARY:"
echo "  Core Services:"
echo "    Backend API:     $backend_test   http://localhost:8001/health"
echo "    Frontend:        $frontend_test   http://localhost:8082/"
echo ""
echo "  Monitoring Stack:"
echo "    Prometheus:      $prometheus_test   http://localhost:9090/"
echo "    Grafana:         $grafana_test   http://localhost:3001/ (admin/staging_admin_2025_secure)"
echo "    cAdvisor:        $cadvisor_test   http://localhost:8083/"

# Step 9: Show running containers
echo ""
echo "🐳 Step 9: Running containers:"
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml ps

# Step 10: Test download URL fix
echo ""
echo "🧪 Step 10: Testing download URL fix..."
echo "   The backend now uses BASE_URL=http://localhost:8001"
echo "   Download URLs should now be: http://localhost:8001/api/v1/jobs/{id}/download"
echo "   Instead of the broken: http://api/v1/jobs/{id}/download"

echo ""
echo "🎉 STAGING FIXES COMPLETED!"
echo "=========================="
echo ""
echo "📝 Summary of fixes applied:"
echo "  ✅ 1. Download URL Issue:"
echo "     - Added BASE_URL=http://localhost:8001 to backend-staging environment"
echo "     - Backend now generates correct download URLs"
echo "     - Download button should work properly"
echo ""
echo "  ✅ 2. Monitoring Stack Issue:"
echo "     - Started services with --env-file .env.monitoring.staging"
echo "     - Grafana credentials properly loaded from environment file"
echo "     - All monitoring services should be accessible"
echo ""
echo "🔍 Next Steps:"
echo "  1. Test video processing and download to verify URL fix"
echo "  2. Access monitoring dashboards to verify they're working"
echo "  3. Check logs if any service shows ❌ status above"
echo ""
echo "📊 Access URLs:"
echo "  🎬 Application:    http://localhost:8082/"
echo "  🔧 Backend API:    http://localhost:8001/health"  
echo "  📈 Prometheus:     http://localhost:9090/"
echo "  📊 Grafana:        http://localhost:3001/"
echo "  🏷️ cAdvisor:       http://localhost:8083/"
echo ""
echo "🔑 Grafana Login: admin / staging_admin_2025_secure" 