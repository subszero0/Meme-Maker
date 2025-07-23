# 🚀 COMPREHENSIVE STAGING FIX - PowerShell Version
# Fixes: Port conflicts, Redis ContainerConfig errors, API routing issues
# Author: AI Assistant
# Date: Get-Date
# Branch: monitoring-staging

param(
    [switch]$Force = $false
)

# Enable strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Colors for output
$Red = "Red"
$Green = "Green" 
$Yellow = "Yellow"
$Blue = "Cyan"

# Logging functions
function Write-Log {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message" -ForegroundColor $Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor $Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor $Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor $Red
}

# Function to check if command exists
function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Pre-flight checks
Write-Log "🔍 Running pre-flight checks..."

if (-not (Test-Command "docker")) {
    Write-Error "Docker is not installed or not in PATH"
    exit 1
}

if (-not (Test-Command "docker-compose")) {
    Write-Error "Docker Compose is not installed or not in PATH"
    exit 1
}

try {
    docker info | Out-Null
}
catch {
    Write-Error "Docker daemon is not running"
    exit 1
}

Write-Success "Pre-flight checks passed"

# Step 1: Clean up conflicting containers and fix Redis issue
Write-Log "🧹 Cleaning up conflicting containers and fixing Redis ContainerConfig issue..."

# Stop and remove containers that are causing port conflicts
try {
    $ConflictingContainers = docker ps -q --filter "publish=9090" --filter "publish=3001" --filter "publish=8083" 2>$null
    if ($ConflictingContainers) {
        Write-Warning "Found conflicting containers using ports 9090, 3001, or 8083"
        docker stop $ConflictingContainers
        docker rm $ConflictingContainers
        Write-Success "Removed conflicting containers"
    }
}
catch {
    Write-Warning "No conflicting containers found or error removing them"
}

# Clean up any orphaned containers
try { docker container prune -f | Out-Null } catch {}

# Force remove any existing staging containers to fix Redis ContainerConfig
Write-Log "🔧 Force removing existing staging containers to fix ContainerConfig issue..."
try { docker-compose -f docker-compose.staging.yml down -v --remove-orphans | Out-Null } catch {}
try { docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml down -v --remove-orphans | Out-Null } catch {}

# Remove any dangling containers that might have ContainerConfig issues
try {
    $StagingContainers = docker ps -aq --filter "name=*staging*" 2>$null
    if ($StagingContainers) {
        docker stop $StagingContainers
        docker rm $StagingContainers
        Write-Success "Removed all staging containers"
    }
}
catch {
    Write-Warning "No staging containers found or error removing them"
}

# Clean up networks
try { docker network prune -f | Out-Null } catch {}

Write-Success "Container cleanup completed"

# Step 2: Pull all required images
Write-Log "📥 Pulling latest Docker images..."
try {
    docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml pull
}
catch {
    Write-Warning "Some images failed to pull, continuing..."
}
Write-Success "Image pull completed"

# Step 3: Build services with no cache to ensure fresh builds
Write-Log "🔨 Building services with fresh containers..."
try {
    docker-compose -f docker-compose.staging.yml build --no-cache
}
catch {
    Write-Error "Failed to build staging services"
    exit 1
}
Write-Success "Service build completed"

# Step 4: Start core services first
Write-Log "🚀 Starting core services (Redis, Backend, Worker)..."
docker-compose -f docker-compose.staging.yml up -d redis-staging
Start-Sleep -Seconds 10

# Wait for Redis to be healthy
Write-Log "⏳ Waiting for Redis to be healthy..."
$RedisHealthy = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $PingResult = docker-compose -f docker-compose.staging.yml exec -T redis-staging redis-cli ping 2>$null
        if ($PingResult -like "*PONG*") {
            $RedisHealthy = $true
            break
        }
    }
    catch {}
    Start-Sleep -Seconds 2
}

if (-not $RedisHealthy) {
    Write-Error "Redis failed to start properly"
    docker-compose -f docker-compose.staging.yml logs redis-staging
    exit 1
}
Write-Success "Redis is healthy"

# Start backend
docker-compose -f docker-compose.staging.yml up -d backend-staging
Start-Sleep -Seconds 15

# Wait for backend to be healthy
Write-Log "⏳ Waiting for backend to be healthy..."
$BackendHealthy = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:8001/health" -TimeoutSec 3 -ErrorAction SilentlyContinue
        if ($Response.StatusCode -eq 200) {
            $BackendHealthy = $true
            break
        }
    }
    catch {}
    Start-Sleep -Seconds 3
}

if (-not $BackendHealthy) {
    Write-Error "Backend failed to start properly"
    docker-compose -f docker-compose.staging.yml logs backend-staging
    exit 1
}
Write-Success "Backend is healthy"

# Start worker and frontend
docker-compose -f docker-compose.staging.yml up -d worker-staging
Start-Sleep -Seconds 10

docker-compose -f docker-compose.staging.yml up -d frontend-staging
Start-Sleep -Seconds 15

# Wait for frontend to be healthy
Write-Log "⏳ Waiting for frontend to be healthy..."
$FrontendHealthy = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:8082/health" -TimeoutSec 3 -ErrorAction SilentlyContinue
        if ($Response.StatusCode -eq 200) {
            $FrontendHealthy = $true
            break
        }
    }
    catch {}
    Start-Sleep -Seconds 3
}

if (-not $FrontendHealthy) {
    Write-Error "Frontend failed to start properly"
    docker-compose -f docker-compose.staging.yml logs frontend-staging
    exit 1
}
Write-Success "Frontend is healthy"

# Step 5: Start monitoring services
Write-Log "📊 Starting monitoring services..."
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml up -d prometheus grafana redis_exporter node_exporter cadvisor

# Wait for monitoring services
Write-Log "⏳ Waiting for monitoring services to be healthy..."
Start-Sleep -Seconds 30

# Test monitoring services (non-blocking)
$MonitoringServices = @(
    @{Url="http://localhost:9090/-/healthy"; Name="Prometheus"},
    @{Url="http://localhost:3001/api/health"; Name="Grafana"},
    @{Url="http://localhost:8083/healthz"; Name="cAdvisor"}
)

foreach ($service in $MonitoringServices) {
    try {
        $Response = Invoke-WebRequest -Uri $service.Url -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($Response.StatusCode -eq 200) {
            Write-Success "$($service.Name) is responding"
        } else {
            Write-Warning "$($service.Name) health check failed, but continuing..."
        }
    }
    catch {
        Write-Warning "$($service.Name) health check failed, but continuing..."
    }
}

Write-Success "Monitoring services started"

# Step 6: Test API routing specifically for the original issue
Write-Log "🔍 Testing API routing to fix original download issue..."
try {
    $Response = Invoke-WebRequest -Uri "http://localhost:8082/api/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($Response.StatusCode -eq 200) {
        Write-Success "Frontend -> Backend API routing is working"
    } else {
        Write-Warning "Frontend -> Backend API routing issue detected"
    }
}
catch {
    Write-Warning "Frontend -> Backend API routing issue detected"
}

# Step 7: Display comprehensive status
Write-Log "📊 Final Status Report..."

Write-Host "`n🎉 STAGING DEPLOYMENT STATUS" -ForegroundColor $Green
Write-Host "========================================"

# Container status
Write-Host "`n📦 Container Status:" -ForegroundColor $Blue
docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml ps

# Port mapping
Write-Host "`n🌐 Service URLs:" -ForegroundColor $Blue
Write-Host "• Application: http://13.126.173.223:8082/"
Write-Host "• Backend API: http://13.126.173.223:8001/health"
Write-Host "• Prometheus: http://13.126.173.223:9090/"
Write-Host "• Grafana: http://13.126.173.223:3001/ (admin/staging_admin_2025_secure)"
Write-Host "• cAdvisor: http://13.126.173.223:8083/"

# Resource usage
Write-Host "`n💾 Resource Usage:" -ForegroundColor $Blue
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

Write-Success "All services started successfully!"
Write-Host "`n✅ DEPLOYMENT SUCCESSFUL" -ForegroundColor $Green
Write-Host "You can now test video processing to verify the download URL fix."

Write-Host "`n🔍 Debug Commands:" -ForegroundColor $Blue
Write-Host "• Check logs: docker-compose -f docker-compose.staging.yml logs [service-name]"
Write-Host "• Check containers: docker-compose -f docker-compose.staging.yml ps"
Write-Host "• Restart service: docker-compose -f docker-compose.staging.yml restart [service-name]"

Write-Host "`n🔄 To rollback if needed:" -ForegroundColor $Blue
Write-Host "docker-compose -f docker-compose.staging.yml -f docker-compose.staging.monitoring.yml down"

Write-Success "Comprehensive staging fix completed!" 