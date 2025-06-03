#!/usr/bin/env pwsh
# Disk Space Cleanup Script for Meme Maker Development
# This script helps clean up various caches and temporary files that accumulate during development

Write-Host "🧹 Starting disk space cleanup for Meme Maker project..." -ForegroundColor Green

# Function to get directory size
function Get-DirectorySize {
    param([string]$Path)
    if (Test-Path $Path) {
        $size = (Get-ChildItem -Path $Path -Recurse -File | Measure-Object -Property Length -Sum).Sum
        return [Math]::Round($size / 1MB, 2)
    }
    return 0
}

# Function to remove directory safely
function Remove-DirectorySafe {
    param([string]$Path, [string]$Description)
    if (Test-Path $Path) {
        $sizeBefore = Get-DirectorySize $Path
        try {
            Remove-Item -Path $Path -Recurse -Force -ErrorAction Stop
            Write-Host "  ✅ Cleaned $Description (${sizeBefore}MB)" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ Failed to clean $Description : $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "  ℹ️  $Description not found" -ForegroundColor Yellow
    }
}

$totalSaved = 0

Write-Host "`n🐳 Docker cleanup..." -ForegroundColor Cyan

# Docker system prune
Write-Host "  📦 Running docker system prune..."
$dockerPrune = docker system prune -f --volumes 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ Docker system prune completed" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Docker system prune failed or Docker not running" -ForegroundColor Yellow
}

# Docker builder cache
Write-Host "  🏗️  Cleaning Docker builder cache..."
$builderPrune = docker builder prune -f 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ Docker builder cache cleaned" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Docker builder prune failed" -ForegroundColor Yellow
}

Write-Host "`n📦 NPM cache cleanup..." -ForegroundColor Cyan

# NPM cache
if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Host "  🗑️  Clearing NPM cache..."
    npm cache clean --force
    Write-Host "  ✅ NPM cache cleared" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  NPM not found" -ForegroundColor Yellow
}

# Frontend node_modules
Remove-DirectorySafe "frontend/node_modules" "Frontend node_modules"

# Root node_modules (if any)
Remove-DirectorySafe "node_modules" "Root node_modules"

Write-Host "`n🐍 Python cleanup..." -ForegroundColor Cyan

# Python cache directories
Remove-DirectorySafe "backend/__pycache__" "Backend Python cache"
Remove-DirectorySafe "backend/app/__pycache__" "App Python cache"
Remove-DirectorySafe "backend/tests/__pycache__" "Tests Python cache"
Remove-DirectorySafe "worker/__pycache__" "Worker Python cache"

# Pytest cache
Remove-DirectorySafe "backend/.pytest_cache" "Pytest cache"

# Python virtual environments (be careful with this one)
$venvPath = ".venv"
if (Test-Path $venvPath) {
    $venvSize = Get-DirectorySize $venvPath
    Write-Host "  ⚠️  Virtual environment found (${venvSize}MB)" -ForegroundColor Yellow
    Write-Host "  ℹ️  To remove venv: Remove-Item .venv -Recurse -Force" -ForegroundColor Yellow
    Write-Host "  ℹ️  Then recreate with: python -m venv .venv" -ForegroundColor Yellow
}

Write-Host "`n🧪 Test artifacts cleanup..." -ForegroundColor Cyan

# Test reports
Remove-DirectorySafe "reports" "Test reports"
Remove-DirectorySafe "backend/htmlcov" "Coverage reports"
Remove-DirectorySafe "frontend/coverage" "Frontend coverage"

# Cypress artifacts
Remove-DirectorySafe "frontend/cypress/screenshots" "Cypress screenshots"
Remove-DirectorySafe "frontend/cypress/videos" "Cypress videos"

# Jest cache
Remove-DirectorySafe "frontend/.next" "Next.js cache"

Write-Host "`n🏗️ Build artifacts cleanup..." -ForegroundColor Cyan

# Build outputs
Remove-DirectorySafe "frontend/out" "Frontend build output"
Remove-DirectorySafe "frontend/.next" "Next.js build cache"
Remove-DirectorySafe "frontend/dist" "Frontend dist"

Write-Host "`n💾 Temporary files cleanup..." -ForegroundColor Cyan

# Windows temp files related to project
$tempPath = $env:TEMP
if (Test-Path $tempPath) {
    Get-ChildItem -Path $tempPath -Name "*meme*" -ErrorAction SilentlyContinue | ForEach-Object {
        $fullPath = Join-Path $tempPath $_
        Remove-DirectorySafe $fullPath "Temp file: $_"
    }
}

# Log files
Remove-DirectorySafe "*.log" "Log files"
Remove-DirectorySafe "backend/*.log" "Backend log files"
Remove-DirectorySafe "worker/*.log" "Worker log files"

Write-Host "`n📊 Current directory sizes:" -ForegroundColor Cyan

$sizes = @{
    "Frontend node_modules" = Get-DirectorySize "frontend/node_modules"
    "Backend __pycache__" = Get-DirectorySize "backend/__pycache__"
    "Virtual environment" = Get-DirectorySize ".venv"
    "Frontend build" = Get-DirectorySize "frontend/out"
    "Reports" = Get-DirectorySize "reports"
}

foreach ($item in $sizes.GetEnumerator()) {
    if ($item.Value -gt 0) {
        Write-Host "  📁 $($item.Key): $($item.Value)MB" -ForegroundColor White
    }
}

Write-Host "`n🚀 Additional cleanup commands you can run manually:" -ForegroundColor Cyan
Write-Host "  🐳 Docker: docker system prune -a --volumes" -ForegroundColor Yellow
Write-Host "  📦 NPM: npm cache clean --force" -ForegroundColor Yellow
Write-Host "  🐍 Python: Remove-Item .venv -Recurse -Force && python -m venv .venv" -ForegroundColor Yellow
Write-Host "  💾 Git: git clean -fdx (removes all untracked files)" -ForegroundColor Red

Write-Host "`n✅ Cleanup completed!" -ForegroundColor Green
Write-Host "💡 Tip: Run this script periodically to keep disk usage low" -ForegroundColor Blue 