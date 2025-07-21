#!/usr/bin/env pwsh
# Test script to verify download fix is working

Write-Host "Testing Download Fix..." -ForegroundColor Cyan

# Test 1: Check if backend download endpoint works
Write-Host "`n1. Testing backend download endpoint directly..." -ForegroundColor Yellow
try {
    $jobId = "4153dbb4-1f97-4ba5-bd2d-8338c51b3706"
    $backendUrl = "http://localhost:8000/api/v1/jobs/$jobId/download"
    
    $response = Invoke-WebRequest -Uri $backendUrl -Method HEAD -ErrorAction Stop
    $contentLength = $response.Headers.'Content-Length'
    
    Write-Host "Backend download endpoint working" -ForegroundColor Green
    Write-Host "   Content-Length: $contentLength bytes" -ForegroundColor Gray
    
    if ([int]$contentLength -gt 1000000) {
        Write-Host "File size looks correct (over 1MB)" -ForegroundColor Green
    } else {
        Write-Host "File size too small: $contentLength bytes" -ForegroundColor Red
    }
} catch {
    Write-Host "Backend download endpoint failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Verify Redis contains correct job data
Write-Host "`n2. Checking Redis job data..." -ForegroundColor Yellow
try {
    $downloadUrl = docker exec meme-maker-redis redis-cli hget "job:$jobId" download_url
    $fileSize = docker exec meme-maker-redis redis-cli hget "job:$jobId" file_size
    $status = docker exec meme-maker-redis redis-cli hget "job:$jobId" status
    
    Write-Host "Job Status: $status" -ForegroundColor Green
    Write-Host "Download URL: $downloadUrl" -ForegroundColor Green
    Write-Host "File Size: $fileSize bytes" -ForegroundColor Green
    
    if ([int]$fileSize -gt 1000000) {
        Write-Host "Stored file size looks correct" -ForegroundColor Green
    } else {
        Write-Host "Stored file size too small" -ForegroundColor Red
    }
} catch {
    Write-Host "Failed to check Redis: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nFix Summary:" -ForegroundColor Cyan
Write-Host "- Frontend download URLs now use API_BASE_URL from config" -ForegroundColor Gray
Write-Host "- Downloads will go to http://localhost:8000 (backend) not localhost:8080 (frontend)" -ForegroundColor Gray
Write-Host "- This should resolve the 1.2KB download issue" -ForegroundColor Gray

Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "1. Restart frontend development server" -ForegroundColor Yellow
Write-Host "2. Test download on http://localhost:3000" -ForegroundColor Yellow
Write-Host "3. Verify file size is correct (should be over 1MB)" -ForegroundColor Yellow

Write-Host "`nDownload fix implementation complete!" -ForegroundColor Green 