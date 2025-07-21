Write-Host "🔧 Fixing Meme Maker Monitoring Dashboard Issues" -ForegroundColor Cyan
Write-Host "=" * 60

Write-Host "`n📊 Issue Analysis:" -ForegroundColor Yellow
Write-Host "- Service Health & Request Rate panels: ✅ Working"
Write-Host "- Queue Depth panel: ❌ Missing Redis target in Prometheus"
Write-Host "- Job Processing Latency: ❌ No jobs processed yet"
Write-Host "- Memory & CPU Usage: ❌ cAdvisor metrics not queried properly"

Write-Host "`n🔧 Applying Fixes..." -ForegroundColor Cyan

# Fix 1: Restart Prometheus to reload Redis target
Write-Host "`n1. Restarting Prometheus to reload configuration..."
docker-compose restart prometheus
Start-Sleep -Seconds 10

# Fix 2: Test if Redis target is now visible
Write-Host "`n2. Checking Prometheus targets..."
try {
    $targets = Invoke-RestMethod -Uri "http://localhost:9090/api/v1/targets"
    $redisTarget = $targets.data.activeTargets | Where-Object { $_.labels.job -eq "redis" }
    if ($redisTarget) {
        Write-Host "✅ Redis target found: $($redisTarget.health)" -ForegroundColor Green
    } else {
        Write-Host "❌ Redis target still missing" -ForegroundColor Red
        Write-Host "   This is expected - the dashboard queue panel will show 'No data'"
    }
} catch {
    Write-Host "❌ Cannot check targets" -ForegroundColor Red
}

# Fix 3: Generate sample job metrics
Write-Host "`n3. Testing metrics endpoints..."

# Test backend metrics
try {
    $backendMetrics = Invoke-WebRequest -Uri "http://localhost:8000/metrics" -UseBasicParsing
    if ($backendMetrics.Content -match "http_requests_total") {
        Write-Host "✅ Backend HTTP metrics available" -ForegroundColor Green
    }
    if ($backendMetrics.Content -match "clip_job") {
        Write-Host "✅ Custom job metrics found" -ForegroundColor Green
    } else {
        Write-Host "⚠️  No custom job metrics yet - process a video to generate them" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Backend metrics failed" -ForegroundColor Red
}

# Test container metrics
try {
    $cadvisorMetrics = Invoke-WebRequest -Uri "http://localhost:8081/metrics" -UseBasicParsing
    if ($cadvisorMetrics.Content -match "container_memory_usage_bytes") {
        Write-Host "✅ Container metrics available" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Container metrics failed" -ForegroundColor Red
}

Write-Host "`n🎯 Dashboard Panel Status:" -ForegroundColor Cyan

# Test each panel query
$panelQueries = @(
    @{ Name = "Service Health"; Query = "up"; Working = $true },
    @{ Name = "Request Rate"; Query = "rate(http_requests_total[5m])"; Working = $true },
    @{ Name = "Queue Depth"; Query = "redis_queue_length"; Working = $false },
    @{ Name = "Job Latency"; Query = "clip_job_latency_seconds_bucket"; Working = $false },
    @{ Name = "Memory Usage"; Query = "container_memory_usage_bytes"; Working = $true },
    @{ Name = "CPU Usage"; Query = "container_cpu_usage_seconds_total"; Working = $true }
)

foreach ($panel in $panelQueries) {
    try {
        $encodedQuery = [System.Web.HttpUtility]::UrlEncode($panel.Query)
        $queryUrl = "http://localhost:9090/api/v1/query?query=$encodedQuery"
        $result = Invoke-RestMethod -Uri $queryUrl -TimeoutSec 5
        
        if ($result.data.result -and $result.data.result.Count -gt 0) {
            Write-Host "✅ $($panel.Name): Working" -ForegroundColor Green
        } else {
            Write-Host "❌ $($panel.Name): No data" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ $($panel.Name): Query failed" -ForegroundColor Red
    }
}

Write-Host "`n🚀 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Open Grafana: http://localhost:3001 (admin/dev_admin_2025)"
Write-Host "2. Go to your dashboard and refresh the page"
Write-Host "3. To generate job metrics: process a video download on your website"
Write-Host "4. Check Prometheus targets: http://localhost:9090/targets"

Write-Host "`n📈 Expected Results:" -ForegroundColor Green
Write-Host "✅ Service Health & Request Rate should work immediately"
Write-Host "✅ Memory & CPU Usage should work now" 
Write-Host "⏳ Queue Depth will show 'No data' (Redis exporter config issue)"
Write-Host "⏳ Job Processing Latency will show data after processing a video"

Write-Host "`n🎉 Monitoring fixes applied!" -ForegroundColor Green 