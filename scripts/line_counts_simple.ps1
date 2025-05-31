# Simple Line Counter for Meme Maker (PowerShell)
param(
    [switch]$Verbose = $false
)

Write-Host "📊 Meme Maker - Line Count Analysis" -ForegroundColor Magenta
Write-Host "=========================================="
Write-Host ""

# Project directories to analyze
$dirs = @("backend", "frontend", "worker", "infra", "scripts", ".github", "docs")
$totalLines = 0

Write-Host "📁 Lines by Component:" -ForegroundColor Blue
Write-Host ""

foreach ($dir in $dirs) {
    if (Test-Path $dir) {
        # Get code files, excluding common build/cache directories
        $files = Get-ChildItem $dir -Recurse -File | Where-Object {
            ($_.Extension -match '\.(py|js|jsx|ts|tsx|yaml|yml|json|sh|ps1|md|toml|ini|conf)$') -and
            ($_.FullName -notlike "*node_modules*") -and
            ($_.FullName -notlike "*__pycache__*") -and
            ($_.FullName -notlike "*.pytest_cache*") -and
            ($_.FullName -notlike "*out*") -and
            ($_.FullName -notlike "*dist*") -and
            ($_.FullName -notlike "*build*") -and
            ($_.FullName -notlike "*.next*") -and
            ($_.FullName -notlike "*.venv*") -and
            ($_.FullName -notlike "*venv*")
        }
        
        $dirLines = 0
        $fileCount = $files.Count
        
        foreach ($file in $files) {
            try {
                $content = Get-Content $file.FullName -ErrorAction SilentlyContinue
                if ($content) {
                    $lines = $content.Count
                    if ($lines -eq $null) { $lines = 1 }
                    $dirLines += $lines
                    
                    if ($Verbose) {
                        Write-Host "  $($file.Name): $lines lines" -ForegroundColor Gray
                    }
                }
            }
            catch {
                if ($Verbose) {
                    Write-Host "  Skipped $($file.Name) (read error)" -ForegroundColor Yellow
                }
            }
        }
        
        $totalLines += $dirLines
        $formattedLines = "{0:N0}" -f $dirLines
        Write-Host ("{0,-12} {1,8} lines ({2} files)" -f $dir, $formattedLines, $fileCount)
        
    } else {
        Write-Host ("{0,-12} {1,8}" -f $dir, "0 (not found)")
    }
}

Write-Host ""
Write-Host "📊 Summary:" -ForegroundColor Green

# Format total with thousands separator
$formattedTotal = "{0:N0}" -f $totalLines
Write-Host "🎯 Total Lines: $formattedTotal" -ForegroundColor Green

# Additional stats
Write-Host ""
Write-Host "📈 Additional Statistics:" -ForegroundColor Cyan

# Count all code files in project
$allFiles = Get-ChildItem . -Recurse -File | Where-Object {
    ($_.Extension -match '\.(py|js|jsx|ts|tsx|yaml|yml|json|sh|ps1|md)$') -and
    ($_.FullName -notlike "*node_modules*") -and
    ($_.FullName -notlike "*__pycache__*") -and
    ($_.FullName -notlike "*.pytest_cache*") -and
    ($_.FullName -notlike "*out*") -and
    ($_.FullName -notlike "*dist*") -and
    ($_.FullName -notlike "*build*") -and
    ($_.FullName -notlike "*.next*") -and
    ($_.FullName -notlike "*.venv*") -and
    ($_.FullName -notlike "*venv*") -and
    ($_.FullName -notlike "*.git*")
}

$totalFiles = $allFiles.Count
Write-Host "Code files: $totalFiles"

# Rough effort estimate
if ($totalLines -gt 0) {
    $effortDays = [Math]::Round($totalLines / 100)
    Write-Host "Estimated effort: ~$effortDays developer-days"
}

Write-Host ""
Write-Host "✅ Line count analysis complete!" -ForegroundColor Green

if (!$Verbose) {
    Write-Host ""
    Write-Host "ℹ️  Run with -Verbose for detailed file breakdowns" -ForegroundColor Blue
} 