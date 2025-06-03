# CURSOR PROMPT 46.0 • Obtain Let's Encrypt certificates for memeit.pro
# Make https://memeit.pro and https://www.memeit.pro serve the backend
# health JSON ({"status":"ok"}) without ERR_SSL_PROTOCOL_ERROR.

Write-Host "Starting Let's Encrypt certificate acquisition for memeit.pro..." -ForegroundColor Green

# ------------------------------------------------------------------
# 1. Verify DNS → instance IP + port reachability
# ------------------------------------------------------------------
Write-Host "1. Verifying DNS and port reachability..." -ForegroundColor Yellow

try {
    $PUBLIC_IP = (Invoke-RestMethod -Uri "https://ifconfig.me/ip" -TimeoutSec 10)
    Write-Host "Lightsail public IP = $PUBLIC_IP" -ForegroundColor Cyan
} catch {
    Write-Host "Could not get public IP. Trying alternative method..." -ForegroundColor Yellow
    try {
        $PUBLIC_IP = (Invoke-RestMethod -Uri "https://ipinfo.io/ip" -TimeoutSec 10)
        Write-Host "Public IP = $PUBLIC_IP" -ForegroundColor Cyan
    } catch {
        Write-Host "Failed to get public IP. Continuing anyway..." -ForegroundColor Red
        $PUBLIC_IP = "unknown"
    }
}

Write-Host "➜ DNS A-records" -ForegroundColor Cyan
try {
    $memeit_ip = (Resolve-DnsName -Name "memeit.pro" -Type A -ErrorAction SilentlyContinue).IPAddress
    $www_memeit_ip = (Resolve-DnsName -Name "www.memeit.pro" -Type A -ErrorAction SilentlyContinue).IPAddress
    Write-Host "  memeit.pro  → $memeit_ip" -ForegroundColor White
    Write-Host "  www.memeit.pro → $www_memeit_ip" -ForegroundColor White
} catch {
    Write-Host "  DNS resolution failed" -ForegroundColor Red
}

Write-Host "➜ Port reachability (checking local ports)" -ForegroundColor Cyan
try {
    $port80 = Test-NetConnection -ComputerName "localhost" -Port 80 -InformationLevel Quiet
    $port443 = Test-NetConnection -ComputerName "localhost" -Port 443 -InformationLevel Quiet
    if ($port80) { Write-Host "  Port 80 open" -ForegroundColor Green }
    if ($port443) { Write-Host "  Port 443 open" -ForegroundColor Green }
} catch {
    Write-Host "  Port check failed" -ForegroundColor Red
}

# ------------------------------------------------------------------
# 2. Ensure a running Caddy container
# ------------------------------------------------------------------
Write-Host "`n2. Checking Caddy container status..." -ForegroundColor Yellow

$CID = (docker ps -q --filter "ancestor=caddy" 2>$null)
if (-not $CID) {
    Write-Host "Starting Caddy container..." -ForegroundColor Cyan
    docker compose -f infra/production/docker-compose.prod.yml up -d --no-deps caddy
    Start-Sleep -Seconds 5
    $CID = (docker ps -q --filter "ancestor=caddy" 2>$null)
}

if ($CID) {
    Write-Host "Caddy container = $CID" -ForegroundColor Green
} else {
    Write-Host "Failed to start Caddy container" -ForegroundColor Red
    exit 1
}

# ------------------------------------------------------------------
# 3. Verify Caddyfile.prod configuration
# ------------------------------------------------------------------
Write-Host "`n3. Verifying Caddyfile.prod configuration..." -ForegroundColor Yellow

$caddyfile_path = "infra/caddy/Caddyfile.prod"
if (Test-Path $caddyfile_path) {
    $content = Get-Content $caddyfile_path -Raw
    Write-Host "Current Caddyfile.prod content:" -ForegroundColor Cyan
    Write-Host $content -ForegroundColor White
    
    # Check if email is configured
    if ($content -match "email\s+admin@memeit\.pro") {
        Write-Host "✅ Email configuration found" -ForegroundColor Green
    } else {
        Write-Host "❌ Email configuration missing, updating..." -ForegroundColor Red
        
        # Update the Caddyfile with proper email configuration
        $new_content = @"
{
    email admin@memeit.pro
}

memeit.pro, www.memeit.pro {
    encode         zstd gzip
    reverse_proxy  backend:8000
}
"@
        Set-Content -Path $caddyfile_path -Value $new_content -Encoding UTF8
        Write-Host "✅ Caddyfile.prod updated with email configuration" -ForegroundColor Green
    }
} else {
    Write-Host "❌ Caddyfile.prod not found at $caddyfile_path" -ForegroundColor Red
    exit 1
}

# ------------------------------------------------------------------
# 4. Rebuild & restart Caddy, wait for ACME
# ------------------------------------------------------------------
Write-Host "`n4. Rebuilding and restarting Caddy..." -ForegroundColor Yellow

Write-Host "Stopping current Caddy container..." -ForegroundColor Cyan
docker compose -f infra/production/docker-compose.prod.yml stop caddy

Write-Host "Starting Caddy with updated configuration..." -ForegroundColor Cyan
docker compose -f infra/production/docker-compose.prod.yml up -d --no-deps --build caddy

Write-Host "⏳ Waiting 120 seconds for certificate issuance..." -ForegroundColor Cyan
$timer = 0
while ($timer -lt 120) {
    Start-Sleep -Seconds 10
    $timer += 10
    Write-Host "  Elapsed: $timer seconds..." -ForegroundColor DarkGray
}

# ------------------------------------------------------------------
# 5. Show fresh Caddy logs – expect "certificate obtained"
# ------------------------------------------------------------------
Write-Host "`n5. Checking Caddy logs for certificate acquisition..." -ForegroundColor Yellow

$CID = (docker ps -q --filter "ancestor=caddy" 2>$null)
if ($CID) {
    Write-Host "Recent Caddy logs:" -ForegroundColor Cyan
    $logs = docker logs $CID --tail 40 2>$null
    Write-Host $logs -ForegroundColor White
    
    if ($logs -match "certificate obtained|successfully obtained") {
        Write-Host "✅ Certificate obtained successfully!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Certificate acquisition not confirmed in logs" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ Caddy container not running" -ForegroundColor Red
}

# ------------------------------------------------------------------
# 6. Test locally & publicly
# ------------------------------------------------------------------
Write-Host "`n6. Testing endpoints..." -ForegroundColor Yellow

Write-Host "➜ Testing local HTTPS endpoint (skipping certificate check)" -ForegroundColor Cyan
try {
    # For PowerShell 5.1 compatibility - disable certificate validation
    [System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
    $response = Invoke-RestMethod -Uri "https://localhost/health" -TimeoutSec 10
    Write-Host "Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Green
} catch {
    Write-Host "Local HTTPS test failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "➜ Testing public HTTPS endpoint https://www.memeit.pro/health (expect HTTP 200)" -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "https://www.memeit.pro/health" -Method HEAD -TimeoutSec 10
    Write-Host "Status: $($response.StatusCode) $($response.StatusDescription)" -ForegroundColor Green
} catch {
    Write-Host "Public HTTPS test failed: $($_.Exception.Message)" -ForegroundColor Red
}

# ------------------------------------------------------------------
# 7. Final container health
# ------------------------------------------------------------------
Write-Host "`n7. Final container health check..." -ForegroundColor Yellow

Write-Host "Container status:" -ForegroundColor Cyan
$containers = docker ps --format "table {{.Names}}\t{{.Status}}"
Write-Host $containers -ForegroundColor White

# Success criteria summary
Write-Host "`n" + "="*60 -ForegroundColor Green
Write-Host "SUCCESS CRITERIA CHECK:" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Green

Write-Host "• Caddy logs contain 'certificate obtained': " -NoNewline -ForegroundColor White
if ($logs -match "certificate obtained|successfully obtained") {
    Write-Host "✅ PASS" -ForegroundColor Green
} else {
    Write-Host "❌ FAIL" -ForegroundColor Red
}

Write-Host "• Local HTTPS endpoint → {'status':'ok'}: " -NoNewline -ForegroundColor White
try {
    [System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
    $test_response = Invoke-RestMethod -Uri "https://localhost/health" -TimeoutSec 5
    if ($test_response.status -eq "ok") {
        Write-Host "✅ PASS" -ForegroundColor Green
    } else {
        Write-Host "❌ FAIL" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ FAIL" -ForegroundColor Red
}

Write-Host "• Public HTTPS endpoint shows HTTP 200: " -NoNewline -ForegroundColor White
try {
    $test_response = Invoke-WebRequest -Uri "https://www.memeit.pro/health" -Method HEAD -TimeoutSec 10
    if ($test_response.StatusCode -eq 200) {
        Write-Host "✅ PASS" -ForegroundColor Green
    } else {
        Write-Host "❌ FAIL (Status: $($test_response.StatusCode))" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ FAIL (Error: $($_.Exception.Message))" -ForegroundColor Red
}

Write-Host "`nScript completed!" -ForegroundColor Green 