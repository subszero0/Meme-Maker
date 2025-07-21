#!/usr/bin/env powershell

Write-Host "Meme Maker Monitoring Status Check" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Test container status
Write-Host "`n Container Status:" -ForegroundColor Yellow
docker-compose ps | Select-String "meme-maker"

# Test network connectivity 
Write-Host "`n Network Connectivity:" -ForegroundColor Yellow
try {
    $metricsTest = docker exec meme-maker-prometheus-dev wget -q -O - http://backend:8000/metrics 2>$null
    if ($metricsTest) {
        Write-Host "✅ Prometheus → Backend: Connected" -ForegroundColor Green
    } else {
        Write-Host "❌ Prometheus → Backend: Failed" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Prometheus → Backend: Error - $($_.Exception.Message)" -ForegroundColor Red
}

# Test Prometheus health
Write-Host "`n Service Health:" -ForegroundColor Yellow
try {
    $prometheusHealth = Invoke-RestMethod -Uri "http://localhost:9090/-/healthy" -TimeoutSec 5
    Write-Host "✅ Prometheus: Healthy" -ForegroundColor Green
} catch {
    Write-Host "❌ Prometheus: $($_.Exception.Message)" -ForegroundColor Red
}

try {
    $grafanaHealth = Invoke-RestMethod -Uri "http://localhost:3001/api/health" -TimeoutSec 5
    Write-Host "✅ Grafana: Healthy (v$($grafanaHealth.version))" -ForegroundColor Green
} catch {
    Write-Host "❌ Grafana: $($_.Exception.Message)" -ForegroundColor Red
}

try {
    $backendHealth = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host "✅ Backend: Healthy" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend: $($_.Exception.Message)" -ForegroundColor Red
}

# Test metrics collection
Write-Host "`n Metrics Collection:" -ForegroundColor Yellow
try {
    $metrics = Invoke-RestMethod -Uri "http://localhost:8000/metrics" -TimeoutSec 5
    $httpRequests = ($metrics -split "`n" | Select-String "http_requests_total").Count
    if ($httpRequests -gt 0) {
        Write-Host "✅ Backend metrics: $httpRequests HTTP request metrics found" -ForegroundColor Green
    } else {
        Write-Host "Warning: Backend metrics: No HTTP request metrics found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Backend metrics: $($_.Exception.Message)" -ForegroundColor Red
}

# Show network configuration
Write-Host "`n Backend Networks:" -ForegroundColor Yellow
try {
    $networks = docker inspect meme-maker-backend --format="{{json .NetworkSettings.Networks}}" | ConvertFrom-Json
    foreach ($networkName in $networks.PSObject.Properties.Name) {
        $network = $networks.$networkName
        Write-Host "  Network: $networkName - IP: $($network.IPAddress)" -ForegroundColor White
    }
} catch {
    Write-Host "❌ Network inspection failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n Quick Access URLs:" -ForegroundColor Yellow
Write-Host "  Prometheus: http://localhost:9090" -ForegroundColor White
Write-Host "  Grafana: http://localhost:3001 (admin/dev_admin_2025)" -ForegroundColor White
Write-Host "  Backend: http://localhost:8000" -ForegroundColor White
Write-Host "  Frontend: http://localhost:8080" -ForegroundColor White

Write-Host "`n Monitoring Status Check Complete!" -ForegroundColor Green 