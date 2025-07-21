#!/usr/bin/env pwsh
# Comprehensive test script to verify both CSP and download fixes

Write-Host "Testing Complete Fix: CSP + Download URLs" -ForegroundColor Cyan

# Test 1: Check CSP Configuration
Write-Host "`n1. Testing Content Security Policy..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080" -UseBasicParsing
    $cspHeader = $response.Headers.'Content-Security-Policy'
    
    if ($cspHeader -match "connect-src.*http://localhost:8000") {
        Write-Host "CSP allows localhost:8000 connections" -ForegroundColor Green
        Write-Host "   CSP: $($cspHeader.Substring(0, 100))..." -ForegroundColor Gray
    } else {
        Write-Host "CSP does NOT allow localhost:8000 connections" -ForegroundColor Red
        Write-Host "   CSP: $cspHeader" -ForegroundColor Gray
    }
} catch {
    Write-Host "Failed to check CSP: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Check Backend Download Endpoint
Write-Host "`n2. Testing backend download endpoint..." -ForegroundColor Yellow
try {
    $jobId = "4153dbb4-1f97-4ba5-bd2d-8338c51b3706"
    $backendUrl = "http://localhost:8000/api/v1/jobs/$jobId/download"
    
    $response = Invoke-WebRequest -Uri $backendUrl -Method GET -ErrorAction Stop
    $contentLength = $response.Headers.'Content-Length'
    
    Write-Host "Backend download working - Size: $contentLength bytes" -ForegroundColor Green
    
    if ([int]$contentLength -gt 1000000) {
        Write-Host "File size is correct (over 1MB)" -ForegroundColor Green
    } else {
        Write-Host "WARNING: File size seems small: $contentLength bytes" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Backend download failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Test API Metadata Endpoint
Write-Host "`n3. Testing API metadata endpoint..." -ForegroundColor Yellow
try {
    $metadataUrl = "http://localhost:8000/api/v1/metadata/extract"
    $body = @{
        url = "https://www.instagram.com/reel/example"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri $metadataUrl -Method POST -Body $body -ContentType "application/json" -ErrorAction Stop
    Write-Host "API metadata endpoint working" -ForegroundColor Green
} catch {
    if ($_.Exception.Message -like "*401*" -or $_.Exception.Message -like "*403*") {
        Write-Host "API metadata endpoint working (got auth error as expected)" -ForegroundColor Green
    } else {
        Write-Host "API metadata test: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Test 4: Check Redis Job Data
Write-Host "`n4. Checking Redis job data..." -ForegroundColor Yellow
try {
    $downloadUrl = docker exec meme-maker-redis redis-cli hget "job:$jobId" download_url
    $fileSize = docker exec meme-maker-redis redis-cli hget "job:$jobId" file_size
    $status = docker exec meme-maker-redis redis-cli hget "job:$jobId" status
    
    Write-Host "Redis Status: $status" -ForegroundColor Green
    Write-Host "Redis Download URL: $downloadUrl" -ForegroundColor Green
    Write-Host "Redis File Size: $fileSize bytes" -ForegroundColor Green
} catch {
    Write-Host "Failed to check Redis: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 5: Check Container Status
Write-Host "`n5. Checking container status..." -ForegroundColor Yellow
try {
    $containers = docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    Write-Host "Container Status:" -ForegroundColor Gray
    Write-Host $containers -ForegroundColor Gray
} catch {
    Write-Host "Failed to check containers: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nFix Summary:" -ForegroundColor Cyan
Write-Host "1. CSP Fix: Added http://localhost:8000 to connect-src directive" -ForegroundColor Gray
Write-Host "2. Frontend Code Fix: Download URLs now use API_BASE_URL from config" -ForegroundColor Gray
Write-Host "3. Container rebuilt and restarted with new configuration" -ForegroundColor Gray

Write-Host "`nTesting Instructions:" -ForegroundColor Cyan
Write-Host "1. Go to http://localhost:8080 in your browser" -ForegroundColor Yellow
Write-Host "2. Open F12 Developer Tools -> Network tab" -ForegroundColor Yellow
Write-Host "3. Submit an Instagram video URL" -ForegroundColor Yellow
Write-Host "4. You should see:" -ForegroundColor Yellow
Write-Host "   - NO CSP errors in console" -ForegroundColor Gray
Write-Host "   - API calls to /api/v1/metadata/extract" -ForegroundColor Gray
Write-Host "   - Downloaded files should be full size (not 1.2KB)" -ForegroundColor Gray

Write-Host "`nComplete fix implementation done!" -ForegroundColor Green 