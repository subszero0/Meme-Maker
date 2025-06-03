# Simple Disk Space Cleanup Script for Meme Maker
Write-Host "Starting cleanup..." -ForegroundColor Green

# Docker cleanup
Write-Host "Cleaning Docker..." -ForegroundColor Cyan
docker system prune -f --volumes 2>$null
if ($?) { Write-Host "Docker cleaned successfully" -ForegroundColor Green }

# NPM cleanup
Write-Host "Cleaning NPM..." -ForegroundColor Cyan
if (Get-Command npm -ErrorAction SilentlyContinue) {
    npm cache clean --force 2>$null
    if ($?) { Write-Host "NPM cache cleaned successfully" -ForegroundColor Green }
}

# Remove build artifacts
Write-Host "Cleaning build artifacts..." -ForegroundColor Cyan
$pathsToClean = @(
    "frontend/node_modules",
    "node_modules", 
    "backend/__pycache__",
    "backend/app/__pycache__",
    "backend/tests/__pycache__",
    "worker/__pycache__",
    "backend/.pytest_cache",
    "reports",
    "backend/htmlcov",
    "frontend/coverage",
    "frontend/cypress/screenshots",
    "frontend/cypress/videos",
    "frontend/out",
    "frontend/.next",
    "frontend/dist"
)

foreach ($path in $pathsToClean) {
    if (Test-Path $path) {
        Remove-Item -Path $path -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "Cleaned $path" -ForegroundColor Green
    }
}

Write-Host "Cleanup completed successfully!" -ForegroundColor Green 