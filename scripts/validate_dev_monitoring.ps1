Write-Host "🔍 Validating Development Monitoring Stack..." -ForegroundColor Cyan

# Test all endpoints with development settings
Write-Host "Testing Prometheus health..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:9090/-/healthy" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Prometheus health check passed" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Dev Prometheus failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Testing Grafana health..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3001/api/health" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Grafana health check passed" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Dev Grafana failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Testing backend metrics..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/metrics" -UseBasicParsing
    if ($response.Content -match "clip_jobs_queued_total" -or $response.Content -match "http_requests_total") {
        Write-Host "✅ Backend metrics check passed" -ForegroundColor Green
    } else {
        Write-Host "❌ Backend metrics validation failed - metrics not found" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Dev metrics failed: $_" -ForegroundColor Red
    exit 1
}

# Test development-specific features
Write-Host "Testing Prometheus query API..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/query?query=up" -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    if ($data.data.result.Count -gt 0) {
        Write-Host "✅ Prometheus query API check passed" -ForegroundColor Green
    } else {
        Write-Host "❌ No metrics found in Prometheus" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Dev Prometheus query failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Testing Redis exporter..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:9121/metrics" -UseBasicParsing
    if ($response.Content -match "redis_up" -or $response.Content -match "redis_connected_clients") {
        Write-Host "✅ Redis exporter check passed" -ForegroundColor Green
    } else {
        Write-Host "❌ Redis exporter metrics not found" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Redis exporter failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Testing Node exporter..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:9100/metrics" -UseBasicParsing
    if ($response.Content -match "node_" -or $response.Content -match "go_info") {
        Write-Host "✅ Node exporter check passed" -ForegroundColor Green
    } else {
        Write-Host "❌ Node exporter metrics not found" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Node exporter failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Testing cAdvisor..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8081/metrics" -UseBasicParsing
    if ($response.Content -match "container_cpu_usage_seconds_total" -or $response.Content -match "container_memory_usage_bytes") {
        Write-Host "✅ cAdvisor check passed" -ForegroundColor Green
    } else {
        Write-Host "❌ cAdvisor metrics not found" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ cAdvisor failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Development monitoring stack validated!" -ForegroundColor Green
Write-Host "🎯 Development URLs:" -ForegroundColor Cyan
Write-Host "  Prometheus: http://localhost:9090" -ForegroundColor White
Write-Host "  Grafana: http://localhost:3001 (admin/dev_admin_2025)" -ForegroundColor White
Write-Host "  Redis Exporter: http://localhost:9121/metrics" -ForegroundColor White
Write-Host "  Node Exporter: http://localhost:9100/metrics" -ForegroundColor White
Write-Host "  cAdvisor: http://localhost:8081/metrics" -ForegroundColor White 