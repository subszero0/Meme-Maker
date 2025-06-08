# 🚀 Quick Test Runner - Unit Tests Only (Windows PowerShell)
# Goal: Complete in < 1 minute for fast developer feedback

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting quick test run (unit tests only)..." -ForegroundColor Green
Write-Host "⏱️  Expected runtime: < 1 minute" -ForegroundColor Cyan
Write-Host ""

# Start timing
$start_time = Get-Date

try {
    # Backend Unit Tests
    Write-Host "🐍 Running backend unit tests..." -ForegroundColor Yellow
    Set-Location backend
    python -m pytest tests/test_business_logic.py tests/test_simple.py -v --tb=short -q
    Write-Host "✅ Backend unit tests passed" -ForegroundColor Green
    Write-Host ""

    # Frontend Unit Tests
    Write-Host "🟨 Running frontend unit tests..." -ForegroundColor Yellow
    Set-Location ../frontend
    npm test -- --passWithNoTests --watchAll=false --silent
    Write-Host "✅ Frontend unit tests passed" -ForegroundColor Green
    Write-Host ""

    # Calculate runtime
    $end_time = Get-Date
    $runtime = ($end_time - $start_time).TotalSeconds

    Write-Host "🎉 Quick tests completed successfully!" -ForegroundColor Green
    Write-Host "⏱️  Runtime: $([math]::Round($runtime, 1)) seconds" -ForegroundColor Cyan

    if ($runtime -lt 60) {
        Write-Host "🎯 Target achieved: < 1 minute ✅" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Runtime exceeded 1 minute target" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "❌ Tests failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
finally {
    # Return to original directory
    Set-Location ..
} 