# Prometheus & Grafana Complete Functionality Guide

**Created**: 2025-07-21 19:07:51  
**Environment**: Development (localhost)  
**Status**: Comprehensive reference guide

---

## 🎯 **Quick Access URLs**

| Service | URL | Credentials | Purpose |
|---------|-----|-------------|---------|
| **Grafana** | http://localhost:3001 | admin/dev_admin_2025 | Dashboards & Visualizations |
| **Prometheus** | http://localhost:9090 | None | Metrics Query & Targets |
| **Backend Metrics** | http://localhost:8000/metrics | None | Raw metrics endpoint |
| **Redis Exporter** | http://localhost:9121/metrics | None | Redis metrics |
| **Node Exporter** | http://localhost:9100/metrics | None | System metrics |
| **cAdvisor** | http://localhost:8081/metrics | None | Container metrics |

---

## 🔧 **PowerShell Commands for Monitoring**

### **Basic Setup & Management**

```powershell
# Start monitoring stack
docker-compose -f docker-compose.yaml -f docker-compose.monitoring.override.yml up -d

# Check all monitoring services status
docker-compose ps | Select-String "prometheus|grafana|redis_exporter|node_exporter|cadvisor"

# View logs for troubleshooting
docker-compose logs grafana
docker-compose logs prometheus
docker-compose logs redis_exporter

# Restart specific services
docker-compose restart grafana
docker-compose restart prometheus

# Stop monitoring stack (preserve data)
docker-compose -f docker-compose.yaml -f docker-compose.monitoring.override.yml down

# Remove everything including volumes (DANGER - loses all data)
docker-compose -f docker-compose.yaml -f docker-compose.monitoring.override.yml down -v
```

### **Health Checks & Validation**

```powershell
# Quick health check of all services
function Test-MonitoringStack {
    Write-Host "🔍 Testing Monitoring Stack..." -ForegroundColor Cyan
    
    # Test Prometheus
    try {
        $prom = Invoke-WebRequest -Uri "http://localhost:9090/-/healthy" -UseBasicParsing
        Write-Host "✅ Prometheus: $($prom.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "❌ Prometheus: Failed" -ForegroundColor Red
    }
    
    # Test Grafana
    try {
        $grafana = Invoke-WebRequest -Uri "http://localhost:3001/api/health" -UseBasicParsing
        Write-Host "✅ Grafana: $($grafana.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "❌ Grafana: Failed" -ForegroundColor Red
    }
    
    # Test Backend Metrics
    try {
        $metrics = Invoke-WebRequest -Uri "http://localhost:8000/metrics" -UseBasicParsing
        if ($metrics.Content -match "clip_jobs_queued_total") {
            Write-Host "✅ Backend Metrics: Available" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Backend Metrics: Missing custom metrics" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ Backend Metrics: Failed" -ForegroundColor Red
    }
    
    # Test Redis Exporter
    try {
        $redis = Invoke-WebRequest -Uri "http://localhost:9121/metrics" -UseBasicParsing
        Write-Host "✅ Redis Exporter: $($redis.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "❌ Redis Exporter: Failed" -ForegroundColor Red
    }
}

# Run the health check
Test-MonitoringStack
```

### **Prometheus Query Commands**

```powershell
# Function to query Prometheus
function Invoke-PrometheusQuery {
    param(
        [string]$Query,
        [string]$PrometheusUrl = "http://localhost:9090"
    )
    
    $encodedQuery = [System.Web.HttpUtility]::UrlEncode($Query)
    $url = "$PrometheusUrl/api/v1/query?query=$encodedQuery"
    
    try {
        $response = Invoke-RestMethod -Uri $url -Method Get
        return $response.data.result
    } catch {
        Write-Host "❌ Query failed: $_" -ForegroundColor Red
        return $null
    }
}

# Example queries
$upServices = Invoke-PrometheusQuery -Query "up"
$queueDepth = Invoke-PrometheusQuery -Query "redis_queue_length"
$httpRequests = Invoke-PrometheusQuery -Query "rate(http_requests_total[5m])"
$jobLatency = Invoke-PrometheusQuery -Query "histogram_quantile(0.95, rate(clip_job_latency_seconds_bucket[5m]))"

# Display results
Write-Host "📊 Current Metrics:" -ForegroundColor Cyan
Write-Host "Up Services: $($upServices.Count)"
Write-Host "Queue Depth: $($queueDepth[0].value[1])"
```

### **Grafana API Commands**

```powershell
# Grafana API functions
$grafanaUrl = "http://localhost:3001"
$grafanaAuth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("admin:dev_admin_2025"))

function Get-GrafanaDashboards {
    $headers = @{ "Authorization" = "Basic $grafanaAuth" }
    
    try {
        $dashboards = Invoke-RestMethod -Uri "$grafanaUrl/api/search" -Headers $headers
        return $dashboards
    } catch {
        Write-Host "❌ Failed to get dashboards: $_" -ForegroundColor Red
        return $null
    }
}

function Get-GrafanaDataSources {
    $headers = @{ "Authorization" = "Basic $grafanaAuth" }
    
    try {
        $datasources = Invoke-RestMethod -Uri "$grafanaUrl/api/datasources" -Headers $headers
        return $datasources
    } catch {
        Write-Host "❌ Failed to get datasources: $_" -ForegroundColor Red
        return $null
    }
}

# Test Grafana connectivity
$dashboards = Get-GrafanaDashboards
$datasources = Get-GrafanaDataSources

Write-Host "📈 Grafana Status:" -ForegroundColor Cyan
Write-Host "Dashboards: $($dashboards.Count)"
Write-Host "Data Sources: $($datasources.Count)"
```

### **Performance Monitoring Commands**

```powershell
# Monitor container resource usage
function Get-ContainerStats {
    $containers = @("meme-maker-prometheus-dev", "meme-maker-grafana-dev", "meme-maker-redis-exporter", "meme-maker-node-exporter", "meme-maker-cadvisor")
    
    Write-Host "📊 Container Resource Usage:" -ForegroundColor Cyan
    foreach ($container in $containers) {
        try {
            $stats = docker stats $container --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
            Write-Host $stats
        } catch {
            Write-Host "❌ Failed to get stats for $container" -ForegroundColor Red
        }
    }
}

# Monitor disk usage for prometheus data
function Get-PrometheusStorageUsage {
    $volumeInfo = docker volume inspect meme-maker_prometheus_data | ConvertFrom-Json
    $mountpoint = $volumeInfo[0].Mountpoint
    
    Write-Host "💾 Prometheus Storage Usage:" -ForegroundColor Cyan
    Write-Host "Location: $mountpoint"
    
    # Get size using docker system df
    $diskUsage = docker system df -v | Select-String "prometheus_data"
    Write-Host $diskUsage
}

# Run performance monitoring
Get-ContainerStats
Get-PrometheusStorageUsage
```

---

## 🔍 **Troubleshooting Missing Metrics**

### **Issue Analysis: Why Some Panels Aren't Updating**

Based on your description that only "Service Health" and "Request Rate" are working, here are the likely causes:

#### **1. Missing Redis Queue Metrics**
```powershell
# Check if Redis exporter is providing queue metrics
$redisMetrics = Invoke-WebRequest -Uri "http://localhost:9121/metrics" -UseBasicParsing
if ($redisMetrics.Content -match "redis_queue_length") {
    Write-Host "✅ Redis queue metrics available" -ForegroundColor Green
} else {
    Write-Host "❌ Redis queue metrics missing" -ForegroundColor Red
    Write-Host "🔧 Fix: Check Redis exporter configuration" -ForegroundColor Yellow
}
```

#### **2. Missing Container Metrics (cAdvisor)**
```powershell
# Check if cAdvisor is providing container metrics
try {
    $cadvisorMetrics = Invoke-WebRequest -Uri "http://localhost:8081/metrics" -UseBasicParsing
    if ($cadvisorMetrics.Content -match "container_memory_usage_bytes") {
        Write-Host "✅ Container metrics available" -ForegroundColor Green
    } else {
        Write-Host "❌ Container metrics missing" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ cAdvisor not accessible" -ForegroundColor Red
    Write-Host "🔧 Fix: Start cAdvisor container" -ForegroundColor Yellow
}
```

#### **3. Missing Custom Job Metrics**
```powershell
# Check if custom job metrics are being exposed
$backendMetrics = Invoke-WebRequest -Uri "http://localhost:8000/metrics" -UseBasicParsing
$customMetrics = @("clip_job_latency_seconds", "clip_jobs_inflight", "clip_jobs_queued_total")

foreach ($metric in $customMetrics) {
    if ($backendMetrics.Content -match $metric) {
        Write-Host "✅ $metric available" -ForegroundColor Green
    } else {
        Write-Host "❌ $metric missing" -ForegroundColor Red
    }
}
```

### **Common Fixes**

#### **Fix 1: Ensure All Exporters Are Running**
```powershell
# Start missing exporters
docker-compose -f docker-compose.yaml -f docker-compose.monitoring.override.yml up -d redis_exporter node_exporter cadvisor

# Verify they're running
docker-compose ps | Select-String "exporter|cadvisor"
```

#### **Fix 2: Verify Prometheus Target Configuration**
```powershell
# Check Prometheus targets
$targets = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/targets" -UseBasicParsing | ConvertFrom-Json

Write-Host "🎯 Prometheus Targets:" -ForegroundColor Cyan
foreach ($target in $targets.data.activeTargets) {
    $status = if ($target.health -eq "up") { "✅" } else { "❌" }
    Write-Host "$status $($target.labels.job): $($target.scrapeUrl) - $($target.health)"
}
```

#### **Fix 3: Restart Prometheus to Reload Configuration**
```powershell
# Reload Prometheus configuration
docker-compose restart prometheus

# Wait for startup
Start-Sleep -Seconds 10

# Test targets again
Invoke-WebRequest -Uri "http://localhost:9090/api/v1/targets" -UseBasicParsing
```

#### **Fix 4: Generate Sample Data for Testing**
```powershell
# Create a test job to generate metrics
function New-TestJob {
    $jobData = @{
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        in_ts = 0
        out_ts = 30
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/jobs" -Method Post -Body $jobData -ContentType "application/json"
        Write-Host "✅ Test job created: $($response.job_id)" -ForegroundColor Green
        return $response.job_id
    } catch {
        Write-Host "❌ Failed to create test job: $_" -ForegroundColor Red
        return $null
    }
}

# Create test job to generate metrics
$testJobId = New-TestJob
if ($testJobId) {
    Write-Host "🔄 Processing job to generate metrics..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
    
    # Check if metrics updated
    $metricsAfter = Invoke-WebRequest -Uri "http://localhost:8000/metrics" -UseBasicParsing
    Write-Host "📈 Check metrics at: http://localhost:8000/metrics" -ForegroundColor Cyan
}
```

---

## 📊 **Understanding the Dashboard Panels**

### **Panel Breakdown & Expected Metrics**

| Panel | Metric Query | Expected Source | Troubleshooting |
|-------|--------------|-----------------|-----------------|
| **Service Health** | `up{job="meme-maker-backend"}` | Prometheus self-check | ✅ Working |
| **Request Rate** | `rate(http_requests_total[5m])` | FastAPI instrumentator | ✅ Working |
| **Queue Depth** | `redis_queue_length{queue="clips"}` | Redis exporter | ❌ **MISSING** |
| **Job Latency** | `histogram_quantile(0.95, rate(clip_job_latency_seconds_bucket[5m]))` | Custom backend metrics | ❌ **MISSING** |
| **Memory Usage** | `container_memory_usage_bytes{name=~"meme-maker-.*"}` | cAdvisor | ❌ **MISSING** |
| **CPU Usage** | `rate(container_cpu_usage_seconds_total[name=~"meme-maker-.*"}[5m])` | cAdvisor | ❌ **MISSING** |

### **Diagnostic Commands for Each Panel**

```powershell
# Test Queue Depth Panel
function Test-QueueDepthMetrics {
    Write-Host "🔍 Testing Queue Depth Metrics..." -ForegroundColor Cyan
    
    # Check Redis exporter
    try {
        $redisMetrics = Invoke-WebRequest -Uri "http://localhost:9121/metrics" -UseBasicParsing
        if ($redisMetrics.Content -match "redis_queue_length") {
            Write-Host "✅ Redis exporter has queue metrics" -ForegroundColor Green
        } else {
            Write-Host "❌ Redis exporter missing queue metrics" -ForegroundColor Red
            Write-Host "💡 Solution: Configure Redis exporter to track queues" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ Redis exporter not accessible" -ForegroundColor Red
        Write-Host "💡 Solution: Start redis_exporter container" -ForegroundColor Yellow
    }
    
    # Check if Prometheus can see Redis metrics
    $queueQuery = Invoke-PrometheusQuery -Query "redis_queue_length"
    if ($queueQuery -and $queueQuery.Count -gt 0) {
        Write-Host "✅ Prometheus can query queue depth" -ForegroundColor Green
    } else {
        Write-Host "❌ Prometheus cannot query queue depth" -ForegroundColor Red
    }
}

# Test Job Latency Panel
function Test-JobLatencyMetrics {
    Write-Host "🔍 Testing Job Latency Metrics..." -ForegroundColor Cyan
    
    # Check backend custom metrics
    $backendMetrics = Invoke-WebRequest -Uri "http://localhost:8000/metrics" -UseBasicParsing
    if ($backendMetrics.Content -match "clip_job_latency_seconds_bucket") {
        Write-Host "✅ Backend has job latency histogram" -ForegroundColor Green
    } else {
        Write-Host "❌ Backend missing job latency histogram" -ForegroundColor Red
        Write-Host "💡 Solution: Process a job to generate metrics" -ForegroundColor Yellow
    }
    
    # Check if Prometheus can see job metrics
    $latencyQuery = Invoke-PrometheusQuery -Query "clip_job_latency_seconds_bucket"
    if ($latencyQuery -and $latencyQuery.Count -gt 0) {
        Write-Host "✅ Prometheus can query job latency" -ForegroundColor Green
    } else {
        Write-Host "❌ Prometheus cannot query job latency" -ForegroundColor Red
    }
}

# Test Container Metrics Panel
function Test-ContainerMetrics {
    Write-Host "🔍 Testing Container Metrics..." -ForegroundColor Cyan
    
    # Check cAdvisor
    try {
        $cadvisorMetrics = Invoke-WebRequest -Uri "http://localhost:8081/metrics" -UseBasicParsing
        if ($cadvisorMetrics.Content -match "container_memory_usage_bytes") {
            Write-Host "✅ cAdvisor has container metrics" -ForegroundColor Green
        } else {
            Write-Host "❌ cAdvisor missing container metrics" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ cAdvisor not accessible" -ForegroundColor Red
        Write-Host "💡 Solution: Start cadvisor container" -ForegroundColor Yellow
    }
    
    # Check if Prometheus can see container metrics
    $containerQuery = Invoke-PrometheusQuery -Query "container_memory_usage_bytes"
    if ($containerQuery -and $containerQuery.Count -gt 0) {
        Write-Host "✅ Prometheus can query container metrics" -ForegroundColor Green
    } else {
        Write-Host "❌ Prometheus cannot query container metrics" -ForegroundColor Red
    }
}

# Run all tests
Test-QueueDepthMetrics
Test-JobLatencyMetrics
Test-ContainerMetrics
```

---

## 🚀 **Complete Setup from Scratch**

### **Step 1: Initial Setup**
```powershell
# Ensure you're in the project directory
Set-Location "C:\Users\Vivek Subramanian\Desktop\Meme Maker - Local\Meme-Maker"

# Create monitoring environment file
@"
GRAFANA_SECRET_KEY=$(openssl rand -hex 32)
PROMETHEUS_RETENTION_TIME=7d
PROMETHEUS_RETENTION_SIZE=2GB
"@ | Out-File -FilePath ".env.monitoring.dev" -Encoding UTF8

# Verify configuration files exist
$configFiles = @(
    "infra/prometheus/prometheus.dev.yml",
    "infra/grafana/dashboards/meme-maker-overview.json",
    "infra/grafana/provisioning/datasources/prometheus.yml",
    "docker-compose.monitoring.override.yml"
)

foreach ($file in $configFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file exists" -ForegroundColor Green
    } else {
        Write-Host "❌ $file missing" -ForegroundColor Red
    }
}
```

### **Step 2: Start Complete Stack**
```powershell
# Pull required images first
docker-compose -f docker-compose.yaml -f docker-compose.monitoring.override.yml pull

# Start the complete stack
docker-compose -f docker-compose.yaml -f docker-compose.monitoring.override.yml up -d

# Wait for services to initialize
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check status
docker-compose ps
```

### **Step 3: Verification**
```powershell
# Run comprehensive verification
.\scripts\validate_dev_monitoring.ps1

# Or run manual verification
Test-MonitoringStack
Test-QueueDepthMetrics
Test-JobLatencyMetrics
Test-ContainerMetrics
```

---

## 🔧 **Advanced PowerShell Functions**

### **Metrics Collection Function**
```powershell
function Get-DetailedMetrics {
    Write-Host "📊 Collecting Detailed Metrics..." -ForegroundColor Cyan
    
    $metrics = @{}
    
    # Prometheus health
    try {
        $promHealth = Invoke-WebRequest -Uri "http://localhost:9090/-/healthy" -UseBasicParsing
        $metrics.PrometheusHealth = $promHealth.StatusCode
    } catch {
        $metrics.PrometheusHealth = "Failed"
    }
    
    # Service uptime
    $upServices = Invoke-PrometheusQuery -Query "up"
    $metrics.ServicesUp = $upServices.Count
    
    # HTTP request rate
    $httpRate = Invoke-PrometheusQuery -Query "rate(http_requests_total[5m])"
    $metrics.HttpRequestRate = if ($httpRate) { $httpRate[0].value[1] } else { 0 }
    
    # Queue depth
    $queueDepth = Invoke-PrometheusQuery -Query "redis_queue_length"
    $metrics.QueueDepth = if ($queueDepth) { $queueDepth[0].value[1] } else { "N/A" }
    
    # Job latency
    $jobLatency = Invoke-PrometheusQuery -Query "histogram_quantile(0.95, rate(clip_job_latency_seconds_bucket[5m]))"
    $metrics.JobLatency95p = if ($jobLatency) { $jobLatency[0].value[1] } else { "N/A" }
    
    # Container memory
    $containerMemory = Invoke-PrometheusQuery -Query "container_memory_usage_bytes"
    $metrics.ContainerMemoryMetrics = if ($containerMemory) { $containerMemory.Count } else { 0 }
    
    # Display results
    Write-Host "`n📈 Current Metrics Summary:" -ForegroundColor Green
    $metrics.GetEnumerator() | Sort-Object Name | ForEach-Object {
        Write-Host "  $($_.Key): $($_.Value)"
    }
    
    return $metrics
}

# Run detailed metrics collection
$currentMetrics = Get-DetailedMetrics
```

### **Log Analysis Function**
```powershell
function Get-MonitoringLogs {
    param(
        [int]$Lines = 50,
        [string]$Service = $null
    )
    
    $services = @("prometheus", "grafana", "redis_exporter", "node_exporter", "cadvisor")
    
    if ($Service) {
        Write-Host "📋 Logs for $Service (last $Lines lines):" -ForegroundColor Cyan
        docker-compose logs --tail=$Lines $Service
    } else {
        foreach ($svc in $services) {
            Write-Host "`n📋 Logs for $svc (last $Lines lines):" -ForegroundColor Cyan
            docker-compose logs --tail=$Lines $svc
            Write-Host "─" * 80
        }
    }
}

# Usage examples:
# Get-MonitoringLogs -Lines 20                    # All services, 20 lines each
# Get-MonitoringLogs -Service "prometheus"        # Just Prometheus logs
```

---

## 🎯 **Next Steps to Fix Your Issue**

Based on your description, here's the exact order to fix your missing metrics:

### **Immediate Actions (PowerShell)**
```powershell
# 1. Verify all containers are running
docker-compose -f docker-compose.yaml -f docker-compose.monitoring.override.yml ps

# 2. Start missing exporters
docker-compose -f docker-compose.yaml -f docker-compose.monitoring.override.yml up -d redis_exporter node_exporter cadvisor

# 3. Check Prometheus targets
Start-Process "http://localhost:9090/targets"

# 4. Generate test data by processing a job
# Visit your localhost website and download an IG video

# 5. Check metrics after processing
Invoke-WebRequest -Uri "http://localhost:8000/metrics" -UseBasicParsing | Select-String "clip_job"

# 6. Verify Grafana can see new metrics
Start-Process "http://localhost:3001/d/your-dashboard-id"
```

Your issue is likely that the **Redis exporter, Node exporter, and cAdvisor containers aren't running**, which provide the metrics for Queue Depth, Memory Usage, and CPU Usage panels. The job processing metrics won't appear until you actually process a job through your application.

Run the PowerShell commands above and let me know what you find! [[memory:3754504]] 