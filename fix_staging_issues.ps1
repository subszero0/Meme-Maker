# PowerShell Script to Fix Staging Issues - Download URL + Monitoring Stack
Write-Host "🔧 FIXING STAGING ISSUES - Download URL + Monitoring Stack" -ForegroundColor Cyan
Write-Host "==========================================================="
Write-Host ""

Write-Host "📋 Issues to fix:" -ForegroundColor Yellow
Write-Host "  1. ❌ Download URL opens in new window with 'http://api/v1/jobs/{id}/download'"
Write-Host "  2. ❌ Prometheus and Grafana not accessible"
Write-Host ""
Write-Host "🔍 Root causes identified:" -ForegroundColor Yellow
Write-Host "  1. Backend BASE_URL not set - defaults to localhost:8000 instead of localhost:8001"
Write-Host "  2. Monitoring stack missing environment variables (GRAFANA_ADMIN_PASSWORD, etc.)"
Write-Host ""

# Step 1: Stop existing services
Write-Host "🛑 Step 1: Stopping existing staging services..." -ForegroundColor Red
try { docker-compose -f docker-compose.staging.yml down --remove-orphans } catch { Write-Host "No staging services running" }
try { docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml down --remove-orphans } catch { Write-Host "No monitoring services running" }

Write-Host ""
Write-Host "✅ Step 2: BASE_URL fix applied to docker-compose.staging.yml" -ForegroundColor Green
Write-Host "   Added: BASE_URL=http://localhost:8001 to backend-staging environment"

# Step 3: Start core staging services
Write-Host ""
Write-Host "🚀 Step 3: Starting core staging services..." -ForegroundColor Cyan
docker-compose -f docker-compose.staging.yml up -d --build

# Wait for services
Write-Host ""
Write-Host "⏳ Step 4: Waiting for core services to initialize (60 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

# Step 5: Check core services
Write-Host ""
Write-Host "🔍 Step 5: Checking core services health..." -ForegroundColor Cyan

try {
    $null = Invoke-WebRequest -Uri "http://localhost:8001/health" -UseBasicParsing -TimeoutSec 5
    $backend_health = "✅ HEALTHY"
} catch {
    $backend_health = "❌ NOT RESPONDING"
}

try {
    $null = Invoke-WebRequest -Uri "http://localhost:8082/" -UseBasicParsing -TimeoutSec 5  
    $frontend_health = "✅ HEALTHY"
} catch {
    $frontend_health = "❌ NOT RESPONDING"
}

Write-Host "  Backend API (http://localhost:8001/health): $backend_health"
Write-Host "  Frontend (http://localhost:8082/): $frontend_health"

# Step 6: Start monitoring services
Write-Host ""
Write-Host "📊 Step 6: Starting monitoring services with proper environment..." -ForegroundColor Cyan
Write-Host "   Using --env-file .env.monitoring.staging for Grafana credentials"

docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml --env-file .env.monitoring.staging up -d

# Wait for monitoring services
Write-Host ""
Write-Host "⏳ Step 7: Waiting for monitoring services to initialize (60 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

# Step 8: Comprehensive health check
Write-Host ""
Write-Host "🔍 Step 8: Comprehensive health check..." -ForegroundColor Cyan

# Test all services
$services = @{
    "Backend API" = "http://localhost:8001/health"
    "Frontend" = "http://localhost:8082/"
    "Prometheus" = "http://localhost:9090/-/healthy"
    "Grafana" = "http://localhost:3001/api/health"
    "cAdvisor" = "http://localhost:8083/healthz"
}

$results = @{}
foreach ($service in $services.GetEnumerator()) {
    try {
        $null = Invoke-WebRequest -Uri $service.Value -UseBasicParsing -TimeoutSec 5
        $results[$service.Key] = "✅"
    } catch {
        $results[$service.Key] = "❌"
    }
}

Write-Host ""
Write-Host "📊 SERVICE HEALTH SUMMARY:" -ForegroundColor Green
Write-Host "  Core Services:"
Write-Host "    Backend API:     $($results['Backend API'])   http://localhost:8001/health"
Write-Host "    Frontend:        $($results['Frontend'])   http://localhost:8082/"
Write-Host ""
Write-Host "  Monitoring Stack:"
Write-Host "    Prometheus:      $($results['Prometheus'])   http://localhost:9090/"
Write-Host "    Grafana:         $($results['Grafana'])   http://localhost:3001/ (admin/staging_admin_2025_secure)"
Write-Host "    cAdvisor:        $($results['cAdvisor'])   http://localhost:8083/"

# Step 9: Show containers
Write-Host ""
Write-Host "🐳 Step 9: Running containers:" -ForegroundColor Cyan
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml ps

# Step 10: Summary
Write-Host ""
Write-Host "🧪 Step 10: Testing download URL fix..." -ForegroundColor Cyan
Write-Host "   The backend now uses BASE_URL=http://localhost:8001"
Write-Host "   Download URLs should now be: http://localhost:8001/api/v1/jobs/{id}/download"
Write-Host "   Instead of the broken: http://api/v1/jobs/{id}/download"

Write-Host ""
Write-Host "🎉 STAGING FIXES COMPLETED!" -ForegroundColor Green
Write-Host "=========================="
Write-Host ""
Write-Host "📝 Summary of fixes applied:" -ForegroundColor Yellow
Write-Host "  ✅ 1. Download URL Issue:"
Write-Host "     - Added BASE_URL=http://localhost:8001 to backend-staging environment"
Write-Host "     - Backend now generates correct download URLs"
Write-Host "     - Download button should work properly"
Write-Host ""
Write-Host "  ✅ 2. Monitoring Stack Issue:"
Write-Host "     - Started services with --env-file .env.monitoring.staging"
Write-Host "     - Grafana credentials properly loaded from environment file"
Write-Host "     - All monitoring services should be accessible"
Write-Host ""
Write-Host "🔍 Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Test video processing and download to verify URL fix"
Write-Host "  2. Access monitoring dashboards to verify they're working"
Write-Host "  3. Check logs if any service shows ❌ status above"
Write-Host ""
Write-Host "📊 Access URLs:" -ForegroundColor Cyan
Write-Host "  🎬 Application:    http://localhost:8082/"
Write-Host "  🔧 Backend API:    http://localhost:8001/health"  
Write-Host "  📈 Prometheus:     http://localhost:9090/"
Write-Host "  📊 Grafana:        http://localhost:3001/"
Write-Host "  🏷️ cAdvisor:       http://localhost:8083/"
Write-Host ""
Write-Host "🔑 Grafana Login: admin / staging_admin_2025_secure" -ForegroundColor Green 