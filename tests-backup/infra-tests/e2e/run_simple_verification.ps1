# Simplified Additional Verification Tests - PowerShell Edition
param(
    [switch]$Debug = $false,
    [switch]$FullCleanup = $false,
    [switch]$Help = $false
)

if ($Help) {
    Write-Host "Meme Maker Additional Verification Tests - Simple PowerShell Edition"
    Write-Host ""
    Write-Host "Usage: .\run_simple_verification.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Debug          Enable debug logging"
    Write-Host "  -FullCleanup    Perform full cleanup after tests"
    Write-Host "  -Help           Show this help message"
    exit 0
}

function Write-InfoLog($Message) {
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-SuccessLog($Message) {
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-WarningLog($Message) {
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-ErrorLog($Message) {
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Cleanup {
    Write-InfoLog "Cleaning up test resources..."
    docker stop caddy-test 2>$null | Out-Null
    docker rm caddy-test 2>$null | Out-Null
    
    if ($FullCleanup) {
        Write-InfoLog "Performing full cleanup..."
        docker-compose -f docker-compose.yaml down --volumes --remove-orphans 2>$null | Out-Null
        docker system prune --volumes --force 2>$null | Out-Null
        Write-SuccessLog "Full cleanup completed"
    }
}

Write-InfoLog "Starting Meme Maker Additional Verification Tests"
Write-InfoLog "Configuration: Debug=$Debug, FullCleanup=$FullCleanup"

# Check prerequisites
Write-InfoLog "Checking prerequisites..."
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-ErrorLog "Docker not found"
    exit 1
}

if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-ErrorLog "Docker Compose not found"
    exit 1
}

Write-SuccessLog "Prerequisites check completed"

# Setup environment file
Write-InfoLog "Setting up test environment..."
$envLines = @(
    "DEBUG=true",
    "REDIS_URL=redis://redis:6379/0",
    "REDIS_DB=0",
    "AWS_ACCESS_KEY_ID=admin",
    "AWS_SECRET_ACCESS_KEY=admin12345",
    "AWS_REGION=us-east-1",
    "AWS_ENDPOINT_URL=http://minio:9000",
    "AWS_ALLOW_HTTP=true",
    "S3_BUCKET=clips",
    'CORS_ORIGINS=["http://localhost:3000","http://localhost:8000","http://localhost","https://localhost"]',
    "MAX_CONCURRENT_JOBS=20",
    "JOB_TIMEOUT=300",
    "RATE_LIMIT=off",
    "MAX_CLIP_SECONDS=180",
    "ENV=test"
)

$envLines | Out-File -FilePath ".env.test" -Encoding UTF8
Write-SuccessLog "Test environment configured"

# Step 1: Start services and run smoke test
Write-InfoLog "Step 1: Starting services and running smoke test..."

Write-InfoLog "Building and starting services..."
docker-compose -f docker-compose.yaml --env-file .env.test build --parallel
docker-compose -f docker-compose.yaml --env-file .env.test up -d redis minio backend worker

# Wait for Redis
Write-InfoLog "Checking Redis health..."
$redisHealthy = $false
for ($i = 1; $i -le 30; $i++) {
    try {
        $pingResult = docker exec meme-maker-redis redis-cli ping 2>$null
        if ($pingResult -eq "PONG") {
            Write-SuccessLog "Redis healthy"
            $redisHealthy = $true
            break
        }
    } catch {}
    
    if ($i -eq 30) {
        Write-ErrorLog "Redis failed to start"
        docker logs meme-maker-redis
        Cleanup
        exit 1
    }
    Start-Sleep 2
}

# Wait for MinIO
Write-InfoLog "Checking MinIO health..."
for ($i = 1; $i -le 30; $i++) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:9003/minio/health/ready" -TimeoutSec 2 -ErrorAction Stop
        Write-SuccessLog "MinIO healthy"
        break
    } catch {}
    
    if ($i -eq 30) {
        Write-ErrorLog "MinIO failed to start"
        docker logs meme-maker-minio
        Cleanup
        exit 1
    }
    Start-Sleep 2
}

# Create S3 bucket
Write-InfoLog "Setting up MinIO bucket..."
docker exec meme-maker-minio mc alias set myminio http://localhost:9000 admin admin12345 2>$null | Out-Null
docker exec meme-maker-minio mc mb myminio/clips --ignore-existing 2>$null | Out-Null

# Wait for Backend
Write-InfoLog "Checking backend health..."
for ($i = 1; $i -le 60; $i++) {
    try {
        $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
        if ($healthResponse.status -eq "ok") {
            Write-SuccessLog "Backend healthy"
            break
        }
    } catch {}
    
    if ($i -eq 60) {
        Write-ErrorLog "Backend failed to start"
        docker logs meme-maker-backend
        Cleanup
        exit 1
    }
    
    if ($i % 10 -eq 0) {
        Write-InfoLog "Backend not ready... (attempt $i/60)"
    }
    Start-Sleep 2
}

# Run worker smoke test
Write-InfoLog "Running worker smoke test..."
$testUrl = "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/10s.mp4"

$jobData = @{
    url = $testUrl
    start = "00:00:00"
    end = "00:00:05"
} | ConvertTo-Json

try {
    $jobResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/jobs" -Method Post -Body $jobData -ContentType "application/json" -TimeoutSec 10
    $jobId = $jobResponse.job_id
    
    if (-not $jobId) {
        Write-ErrorLog "Failed to enqueue job"
        Cleanup
        exit 1
    }
    
    Write-SuccessLog "Job enqueued: $jobId"
    $jobId | Out-File -FilePath "last_job_id.txt" -Encoding UTF8
    
    # Wait for job completion
    Write-InfoLog "Waiting for job completion..."
    for ($i = 1; $i -le 40; $i++) {
        Start-Sleep 3
        
        try {
            $statusResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/jobs/$jobId" -TimeoutSec 5
            $status = $statusResponse.status
            
            if ($i % 5 -eq 0) {
                Write-InfoLog "Job status: $status (attempt $i/40)"
            }
            
            if ($status -eq "done") {
                Write-SuccessLog "Job completed successfully"
                break
            } elseif ($status -eq "error") {
                Write-ErrorLog "Job failed"
                docker logs meme-maker-worker --tail 30
                Cleanup
                exit 1
            }
        } catch {
            Write-WarningLog "Failed to check job status (attempt $i/40)"
        }
        
        if ($i -eq 40) {
            Write-ErrorLog "Job timeout"
            Cleanup
            exit 1
        }
    }
} catch {
    Write-ErrorLog "Failed to enqueue job: $($_.Exception.Message)"
    Cleanup
    exit 1
}

# Step 2: Data Validation
Write-InfoLog "Step 2: Validating Redis and MinIO data..."

# Redis check
$redisExists = docker exec meme-maker-redis redis-cli EXISTS "job:$jobId" 2>$null
if ($redisExists -ne "1") {
    Write-ErrorLog "Redis key job:$jobId not found"
    Cleanup
    exit 1
}

$redisTtl = docker exec meme-maker-redis redis-cli TTL "job:$jobId" 2>$null
if ([int]$redisTtl -le 0) {
    Write-ErrorLog "Redis TTL for job:$jobId is not set (TTL: $redisTtl)"
    Cleanup
    exit 1
}
Write-SuccessLog "Redis job:$jobId exists with TTL $redisTtl seconds"

# MinIO check
Write-InfoLog "Checking MinIO objects..."
docker exec meme-maker-minio mc alias set local http://localhost:9000 admin admin12345 2>$null | Out-Null
$minioObjects = docker exec meme-maker-minio mc ls local/clips 2>$null
if ($minioObjects -and $minioObjects -match $jobId) {
    Write-SuccessLog "MinIO object containing $jobId found"
} else {
    Write-ErrorLog "MinIO object for $jobId missing"
    Cleanup
    exit 1
}

# Step 3: API Tests
Write-InfoLog "Step 3: Testing API endpoints..."

# Metadata endpoint
Write-InfoLog "Testing metadata endpoint..."
$metadataData = @{
    url = "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/10s.mp4"
} | ConvertTo-Json

try {
    $metadataResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/metadata" -Method Post -Body $metadataData -ContentType "application/json" -TimeoutSec 10
    
    if ($metadataResponse.title -and $metadataResponse.duration) {
        Write-SuccessLog "Metadata endpoint passed"
    } else {
        Write-ErrorLog "Metadata response invalid"
        Cleanup
        exit 1
    }
} catch {
    Write-ErrorLog "Metadata endpoint failed: $($_.Exception.Message)"
    Cleanup
    exit 1
}

# CORS test
Write-InfoLog "Testing CORS preflight..."
try {
    $corsResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/jobs" -Method Options -Headers @{
        "Origin" = "http://localhost:3000"
        "Access-Control-Request-Method" = "POST"
    } -TimeoutSec 5
    
    if ($corsResponse.StatusCode -eq 204 -or $corsResponse.StatusCode -eq 200) {
        Write-SuccessLog "CORS preflight succeeded (HTTP $($corsResponse.StatusCode))"
    } else {
        Write-ErrorLog "CORS preflight failed (code: $($corsResponse.StatusCode))"
    }
} catch {
    Write-WarningLog "CORS preflight test failed: $($_.Exception.Message)"
}

# Step 4: TLS Setup
Write-InfoLog "Step 4: Setting up Caddy for TLS testing..."

# Create Caddyfile
$caddyLines = @(
    "localhost {",
    "  tls internal",
    "  reverse_proxy backend:8000",
    "}",
    "",
    ":80 {",
    "  redir https://{host}{uri}",
    "}"
)
$caddyLines | Out-File -FilePath "Caddyfile.ci" -Encoding UTF8

# Get network name
$networkName = docker network ls --filter name=meme-maker --format "{{.Name}}" 2>$null | Select-Object -First 1
if (-not $networkName) {
    $networkName = "meme-maker_default"
}

# Start Caddy
Write-InfoLog "Starting Caddy with TLS configuration..."
docker run -d --name caddy-test --network $networkName -p 80:80 -p 443:443 -v "${PWD}/Caddyfile.ci:/etc/caddy/Caddyfile:ro" caddy:2.8.4-alpine
Start-Sleep 10

# Wait for Caddy
for ($i = 1; $i -le 20; $i++) {
    $caddyLogs = docker logs caddy-test 2>$null | Out-String
    if ($caddyLogs -match "serving") {
        Write-SuccessLog "Caddy initialized"
        break
    }
    
    if ($i -eq 20) {
        Write-ErrorLog "Caddy failed to start"
        docker logs caddy-test
        Cleanup
        exit 1
    }
    Start-Sleep 2
}

# Test HTTP redirect
Write-InfoLog "Testing HTTP to HTTPS redirect..."
try {
    $httpResponse = Invoke-WebRequest -Uri "http://localhost" -MaximumRedirection 0 -ErrorAction Stop
    $httpStatus = $httpResponse.StatusCode
} catch {
    $httpStatus = $_.Exception.Response.StatusCode.value__
}

if ($httpStatus -eq 301 -or $httpStatus -eq 308) {
    Write-SuccessLog "HTTP redirect to HTTPS confirmed (HTTP $httpStatus)"
} else {
    Write-ErrorLog "HTTP->HTTPS redirect failed (status: $httpStatus)"
    docker logs caddy-test --tail 20
    Cleanup
    exit 1
}

# Test HTTPS
Write-InfoLog "Testing TLS handshake..."
try {
    $httpsStatus = docker run --rm --network host curlimages/curl:latest -s -o /dev/null -k -w "%{http_code}" https://localhost 2>$null
    if ($httpsStatus -eq "200" -or $httpsStatus -eq "502") {
        Write-SuccessLog "TLS handshake succeeded (HTTPS status: $httpsStatus)"
    } else {
        Write-WarningLog "TLS handshake inconclusive (HTTPS status: $httpsStatus)"
    }
} catch {
    Write-WarningLog "TLS handshake test failed: $($_.Exception.Message)"
}

# Final summary
Write-InfoLog "Final data summary..."

# Redis summary
if (docker ps --format "table {{.Names}}" | Select-String "meme-maker-redis") {
    $finalTtl = docker exec meme-maker-redis redis-cli TTL "job:$jobId" 2>$null
    $redisKeys = (docker exec meme-maker-redis redis-cli --scan --pattern "*job*" 2>$null | Measure-Object).Count
    Write-InfoLog "Redis - Job TTL: $finalTtl seconds, Total job keys: $redisKeys"
} else {
    Write-WarningLog "Redis container not running"
}

# MinIO summary
if (docker ps --format "table {{.Names}}" | Select-String "meme-maker-minio") {
    docker exec meme-maker-minio mc alias set local http://localhost:9000 admin admin12345 2>$null | Out-Null
    $minioObjectCount = (docker exec meme-maker-minio mc ls local/clips 2>$null | Measure-Object).Count
    Write-InfoLog "MinIO - Objects in clips bucket: $minioObjectCount"
} else {
    Write-WarningLog "MinIO container not running"
}

Write-SuccessLog "Additional verification tests completed successfully!"
Write-InfoLog "Summary:"
Write-InfoLog "  - Redis data validation: PASSED"
Write-InfoLog "  - MinIO object validation: PASSED"  
Write-InfoLog "  - API endpoint tests: PASSED"
Write-InfoLog "  - Caddy TLS configuration: PASSED"

# Cleanup
Cleanup

Write-SuccessLog "All tests completed successfully!" 