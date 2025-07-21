Write-Host "🔍 Meme Maker Monitoring Troubleshoot Script" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

# Function to test web endpoints
function Test-Endpoint {
    param(
        [string]$Url,
        [string]$Name,
        [string]$ExpectedContent = $null
    )
    
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
        if ($ExpectedContent -and $response.Content -match $ExpectedContent) {
            Write-Host "✅ $Name : $($response.StatusCode) (Content verified)" -ForegroundColor Green
            return $true
        } elseif ($response.StatusCode -eq 200) {
            Write-Host "✅ $Name : $($response.StatusCode)" -ForegroundColor Green
            return $true
        } else {
            Write-Host "⚠️ $Name : $($response.StatusCode)" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Host "❌ $Name : Failed ($($_.Exception.Message))" -ForegroundColor Red
        return $false
    }
}

# Function to query Prometheus
function Test-PrometheusQuery {
    param(
        [string]$Query,
        [string]$Description
    )
    
    try {
        $encodedQuery = [System.Web.HttpUtility]::UrlEncode($Query)
        $url = "http://localhost:9090/api/v1/query?query=$encodedQuery"
        $response = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 10
        
        if ($response.data.result -and $response.data.result.Count -gt 0) {
            $value = $response.data.result[0].value[1]
            Write-Host "✅ $Description : $value" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ $Description : No data" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ $Description : Query failed" -ForegroundColor Red
        return $false
    }
}

Write-Host "`n🔍 Step 1: Container Status Check" -ForegroundColor Cyan
Write-Host "-" * 40

# Check if containers are running
$containers = @(
    "meme-maker-backend",
    "meme-maker-prometheus-dev", 
    "meme-maker-grafana-dev",
    "meme-maker-redis-exporter",
    "meme-maker-node-exporter",
    "meme-maker-cadvisor"
)

$runningContainers = @()
foreach ($container in $containers) {
    try {
        $status = docker inspect $container --format "{{.State.Status}}" 2>$null
        if ($status -eq "running") {
            Write-Host "✅ $container : Running" -ForegroundColor Green
            $runningContainers += $container
        } else {
            Write-Host "❌ $container : $status" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ $container : Not found" -ForegroundColor Red
    }
}

Write-Host "`n🌐 Step 2: Service Health Check" -ForegroundColor Cyan
Write-Host "-" * 40

$services = @()
$services += @{ Name = "Prometheus"; Url = "http://localhost:9090/-/healthy"; Content = $null }
$services += @{ Name = "Grafana"; Url = "http://localhost:3001/api/health"; Content = $null }
$services += @{ Name = "Backend Metrics"; Url = "http://localhost:8000/metrics"; Content = "prometheus_client" }
$services += @{ Name = "Redis Exporter"; Url = "http://localhost:9121/metrics"; Content = "redis_up" }
$services += @{ Name = "Node Exporter"; Url = "http://localhost:9100/metrics"; Content = "node_up" }
$services += @{ Name = "cAdvisor"; Url = "http://localhost:8081/metrics"; Content = "container_" }

$healthyServices = 0
foreach ($service in $services) {
    if (Test-Endpoint -Url $service.Url -Name $service.Name -ExpectedContent $service.Content) {
        $healthyServices++
    }
}

Write-Host "`n📊 Step 3: Metrics Availability Check" -ForegroundColor Cyan
Write-Host "-" * 40

# Check specific metrics that the dashboard panels need
$metricsChecks = @()
$metricsChecks += @{ Query = "up"; Description = "Service Health" }
$metricsChecks += @{ Query = "rate(http_requests_total[5m])"; Description = "Request Rate" }
$metricsChecks += @{ Query = "redis_queue_length"; Description = "Queue Depth" }
$metricsChecks += @{ Query = "clip_job_latency_seconds_bucket"; Description = "Job Latency Histogram" }
$metricsChecks += @{ Query = "container_memory_usage_bytes"; Description = "Container Memory" }
$metricsChecks += @{ Query = "container_cpu_usage_seconds_total"; Description = "Container CPU" }

$workingMetrics = 0
foreach ($check in $metricsChecks) {
    if (Test-PrometheusQuery -Query $check.Query -Description $check.Description) {
        $workingMetrics++
    }
}

Write-Host "`n🎯 Step 4: Prometheus Targets Check" -ForegroundColor Cyan
Write-Host "-" * 40

try {
    $targets = Invoke-RestMethod -Uri "http://localhost:9090/api/v1/targets" -TimeoutSec 10
    Write-Host "Prometheus Targets Status:"
    
    foreach ($target in $targets.data.activeTargets) {
        $status = if ($target.health -eq "up") { "✅" } else { "❌" }
        $job = $target.labels.job
        $endpoint = $target.scrapeUrl
        $health = $target.health
        Write-Host "  $status $job : $endpoint ($health)"
    }
} catch {
    Write-Host "❌ Cannot retrieve Prometheus targets" -ForegroundColor Red
}

Write-Host "`n🔧 Step 5: Auto-Fix Recommendations" -ForegroundColor Cyan
Write-Host "-" * 40

# Provide specific fix commands based on what's broken
$missingContainers = $containers | Where-Object { $_ -notin $runningContainers }

if ($missingContainers.Count -gt 0) {
    Write-Host "🚨 Missing containers detected. Run this command to start them:" -ForegroundColor Yellow
    Write-Host "docker-compose -f docker-compose.yaml -f docker-compose.monitoring.override.yml up -d $($missingContainers -join ' ')" -ForegroundColor White
    Write-Host ""
}

if ($workingMetrics -lt 3) {
    Write-Host "🚨 Multiple metrics missing. Try these fixes:" -ForegroundColor Yellow
    Write-Host "1. Restart monitoring stack:" -ForegroundColor White
    Write-Host "   docker-compose -f docker-compose.yaml -f docker-compose.monitoring.override.yml restart" -ForegroundColor White
    Write-Host "2. Check configuration and restart Prometheus:" -ForegroundColor White
    Write-Host "   docker-compose restart prometheus" -ForegroundColor White
    Write-Host "3. Generate test data by processing a job on your website" -ForegroundColor White
    Write-Host ""
}

Write-Host "`n📈 Step 6: Dashboard Verification" -ForegroundColor Cyan
Write-Host "-" * 40

Write-Host "Visit these URLs to verify your setup:"
Write-Host "  🎯 Prometheus: http://localhost:9090/targets" -ForegroundColor White
Write-Host "  📊 Grafana: http://localhost:3001 (admin/dev_admin_2025)" -ForegroundColor White
Write-Host "  📋 Backend Metrics: http://localhost:8000/metrics" -ForegroundColor White

Write-Host "`n📋 Summary" -ForegroundColor Cyan
Write-Host "-" * 40
Write-Host "  Containers Running: $($runningContainers.Count)/$($containers.Count)"
Write-Host "  Services Healthy: $healthyServices/$($services.Count)"
Write-Host "  Metrics Working: $workingMetrics/$($metricsChecks.Count)"

if ($runningContainers.Count -eq $containers.Count -and $healthyServices -eq $services.Count -and $workingMetrics -ge 4) {
    Write-Host "`n🎉 Your monitoring stack looks healthy!" -ForegroundColor Green
    Write-Host "   If panels still don't show data, try processing a job to generate metrics." -ForegroundColor Green
} else {
    Write-Host "`n⚠️ Issues detected. Follow the recommendations above to fix them." -ForegroundColor Yellow
}

Write-Host "`n🔄 To run this script again: .\scripts\troubleshoot_monitoring.ps1" -ForegroundColor Gray 