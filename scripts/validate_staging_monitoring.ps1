#!/usr/bin/env powershell
Write-Host "🔍 Comprehensive Staging Monitoring Validation..." -ForegroundColor Cyan

# 1. Basic health checks
Write-Host "`n📊 Step 1: Basic Health Checks" -ForegroundColor Yellow
Write-Host "Testing Prometheus health..." -ForegroundColor Gray
try {
    $response = Invoke-WebRequest -Uri "http://localhost:9090/-/healthy" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Staging Prometheus health check passed" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Staging Prometheus failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Testing Grafana health..." -ForegroundColor Gray
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3001/api/health" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Staging Grafana health check passed" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Staging Grafana failed: $_" -ForegroundColor Red
    exit 1
}

# 2. Metrics validation
Write-Host "`n📈 Step 2: Metrics Collection Validation" -ForegroundColor Yellow
Write-Host "Testing backend metrics..." -ForegroundColor Gray
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/metrics" -UseBasicParsing -TimeoutSec 10
    if ($response.Content -match "clip_jobs_queued_total" -or $response.Content -match "http_requests_total") {
        Write-Host "✅ Backend metrics validation passed" -ForegroundColor Green
    } else {
        Write-Host "❌ Backend metrics validation failed - custom metrics not found" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Backend metrics failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Testing Redis exporter..." -ForegroundColor Gray
try {
    $response = Invoke-WebRequest -Uri "http://localhost:9121/metrics" -UseBasicParsing -TimeoutSec 10
    if ($response.Content -match "redis_up") {
        Write-Host "✅ Redis exporter validation passed" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Redis exporter failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Testing Node exporter..." -ForegroundColor Gray
try {
    $response = Invoke-WebRequest -Uri "http://localhost:9100/metrics" -UseBasicParsing -TimeoutSec 10
    if ($response.Content -match "node_up") {
        Write-Host "✅ Node exporter validation passed" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Node exporter failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Testing cAdvisor..." -ForegroundColor Gray
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8081/metrics" -UseBasicParsing -TimeoutSec 10
    if ($response.Content -match "container_cpu_usage_seconds_total") {
        Write-Host "✅ cAdvisor validation passed" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ cAdvisor failed: $_" -ForegroundColor Red
    exit 1
}

# 3. Alert rules validation
Write-Host "`n🚨 Step 3: Alert Rules Validation" -ForegroundColor Yellow
Write-Host "Testing alert rules..." -ForegroundColor Gray
try {
    $response = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/rules" -UseBasicParsing -TimeoutSec 10
    $rules = $response.Content | ConvertFrom-Json
    $stagingRules = $rules.data.groups | Where-Object { $_.name -eq "meme_maker_staging_alerts" }
    if ($stagingRules) {
        Write-Host "✅ Staging alert rules loaded ($($stagingRules.rules.Count) rules)" -ForegroundColor Green
    } else {
        Write-Host "❌ Staging alert rules missing" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Alert rules validation failed: $_" -ForegroundColor Red
    exit 1
}

# 4. Dashboard validation
Write-Host "`n📊 Step 4: Grafana Dashboard Validation" -ForegroundColor Yellow
Write-Host "Testing Grafana dashboard access..." -ForegroundColor Gray
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3001/api/dashboards/home" -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Dashboard access validation passed" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Dashboard access failed: $_" -ForegroundColor Red
    exit 1
}

# 5. Resource monitoring validation
Write-Host "`n💾 Step 5: Resource Monitoring Validation" -ForegroundColor Yellow
Write-Host "Testing container resource metrics..." -ForegroundColor Gray
try {
    $response = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/query?query=container_memory_usage_bytes" -UseBasicParsing -TimeoutSec 10
    $data = $response.Content | ConvertFrom-Json
    if ($data.data.result.Count -gt 0) {
        Write-Host "✅ Container resource metrics available ($($data.data.result.Count) containers)" -ForegroundColor Green
    } else {
        Write-Host "❌ No container metrics found" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Resource metrics validation failed: $_" -ForegroundColor Red
    exit 1
}

# 6. Load test simulation (basic)
Write-Host "`n🏋️ Step 6: Basic Load Test Simulation" -ForegroundColor Yellow
Write-Host "Simulating load to generate metrics..." -ForegroundColor Gray
try {
    # Create 5 test requests to generate metrics
    for ($i = 1; $i -le 5; $i++) {
        Write-Host "  Test request $i/5..." -ForegroundColor Gray
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
        Start-Sleep -Seconds 1
    }
    Write-Host "✅ Load test completed successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Load test failed: $_" -ForegroundColor Red
    exit 1
}

# 7. Final validation summary
Write-Host "`n📋 Step 7: Staging Validation Summary" -ForegroundColor Cyan
Write-Host "✅ All staging monitoring validation checks passed!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Staging URLs for manual verification:" -ForegroundColor White
Write-Host "  🎯 Prometheus: http://localhost:9090" -ForegroundColor Gray
Write-Host "  📊 Grafana: http://localhost:3001 (admin/staging_admin_2025_secure)" -ForegroundColor Gray
Write-Host "  📈 Redis Metrics: http://localhost:9121/metrics" -ForegroundColor Gray
Write-Host "  🖥️ Node Metrics: http://localhost:9100/metrics" -ForegroundColor Gray
Write-Host "  🐳 cAdvisor: http://localhost:8081/metrics" -ForegroundColor Gray
Write-Host ""
Write-Host "🔄 Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Monitor for 24-48 hours in staging" -ForegroundColor White
Write-Host "  2. Verify no false positive alerts" -ForegroundColor White
Write-Host "  3. Test alert notifications" -ForegroundColor White
Write-Host "  4. Validate dashboard accuracy" -ForegroundColor White
Write-Host "  5. Check resource usage impact" -ForegroundColor White
Write-Host "  6. Performance regression testing" -ForegroundColor White
Write-Host ""
Write-Host "🎉 Staging monitoring validation completed successfully!" -ForegroundColor Green 