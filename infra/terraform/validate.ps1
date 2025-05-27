# Terraform validation script for Clip Downloader infrastructure (PowerShell)

$ErrorActionPreference = "Stop"

Write-Host "🔍 Validating Terraform configuration..." -ForegroundColor Blue

# Check if terraform is installed
try {
    $null = Get-Command terraform -ErrorAction Stop
} catch {
    Write-Host "❌ Terraform is not installed. Please install Terraform >= 1.6" -ForegroundColor Red
    Write-Host "   Download from: https://www.terraform.io/downloads.html" -ForegroundColor Yellow
    exit 1
}

# Check terraform version
try {
    $tfVersion = (terraform version -json | ConvertFrom-Json).terraform_version
    Write-Host "✅ Terraform version: $tfVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to get Terraform version" -ForegroundColor Red
    exit 1
}

# Format check
Write-Host "🎨 Checking formatting..." -ForegroundColor Blue
try {
    $formatResult = terraform fmt -check -recursive
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Terraform formatting is correct" -ForegroundColor Green
    } else {
        Write-Host "❌ Terraform formatting issues found. Run 'terraform fmt -recursive' to fix." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Failed to check formatting" -ForegroundColor Red
    exit 1
}

# Initialize (without backend)
Write-Host "⚙️ Initializing Terraform..." -ForegroundColor Blue
try {
    terraform init -backend=false
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Terraform initialization failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Failed to initialize Terraform" -ForegroundColor Red
    exit 1
}

# Validate configuration
Write-Host "🔎 Validating configuration..." -ForegroundColor Blue
try {
    terraform validate
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Terraform configuration is valid" -ForegroundColor Green
    } else {
        Write-Host "❌ Terraform validation failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Failed to validate configuration" -ForegroundColor Red
    exit 1
}

# Check for example variables file
if (-not (Test-Path "terraform.tfvars.example")) {
    Write-Host "❌ terraform.tfvars.example not found" -ForegroundColor Red
    exit 1
}

Write-Host "✅ All validation checks passed!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Copy terraform.tfvars.example to terraform.tfvars" -ForegroundColor White
Write-Host "2. Update terraform.tfvars with your VPC and subnet IDs" -ForegroundColor White
Write-Host "3. Run 'terraform plan' to review the infrastructure" -ForegroundColor White
Write-Host "4. Run 'terraform apply' to create the infrastructure" -ForegroundColor White 