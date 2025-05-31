# Terraform Validation Script for Meme Maker Infrastructure (PowerShell)
# Validates Terraform configuration and checks deployment

param(
    [switch]$NoColor
)

# Color functions
function Write-ColorText {
    param(
        [string]$Text,
        [string]$Color = "White"
    )
    if (-not $NoColor) {
        Write-Host $Text -ForegroundColor $Color
    } else {
        Write-Host $Text
    }
}

function Write-Status {
    param(
        [string]$Status,
        [string]$Message
    )
    switch ($Status) {
        "OK" { Write-ColorText "✅ $Message" "Green" }
        "WARN" { Write-ColorText "⚠️  $Message" "Yellow" }
        "ERROR" { Write-ColorText "❌ $Message" "Red" }
        default { Write-Host $Message }
    }
}

# Configuration
$TerraformDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TerraformVarFile = Join-Path $TerraformDir "terraform.tfvars"

Write-ColorText "🔍 Meme Maker Infrastructure Validation" "Blue"
Write-ColorText "========================================" "Blue"
Write-Host ""

# Check if running in correct directory
Write-ColorText "1. Environment Check" "Blue"
if (-not (Test-Path "main.tf")) {
    Write-Status "ERROR" "Not in terraform directory. Please run from infra/terraform/"
    exit 1
}
Write-Status "OK" "Running from correct directory"

# Check Terraform installation
if (-not (Get-Command terraform -ErrorAction SilentlyContinue)) {
    Write-Status "ERROR" "Terraform not installed"
    exit 1
}

try {
    $TerraformVersionJson = terraform version -json | ConvertFrom-Json
    $TerraformVersion = $TerraformVersionJson.terraform_version
    Write-Status "OK" "Terraform installed (version: $TerraformVersion)"
} catch {
    Write-Status "ERROR" "Failed to get Terraform version"
    exit 1
}

# Check minimum version
$RequiredVersion = [System.Version]"1.5.0"
$CurrentVersion = [System.Version]$TerraformVersion
if ($CurrentVersion -lt $RequiredVersion) {
    Write-Status "ERROR" "Terraform version $TerraformVersion < required $RequiredVersion"
    exit 1
}
Write-Status "OK" "Terraform version meets requirements"

# Check AWS CLI
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Status "WARN" "AWS CLI not installed (optional for validation)"
} else {
    try {
        $AwsIdentity = aws sts get-caller-identity 2>$null | ConvertFrom-Json
        $AwsAccount = $AwsIdentity.Account
        Write-Status "OK" "AWS credentials configured (Account: $AwsAccount)"
    } catch {
        Write-Status "WARN" "AWS credentials not configured"
    }
}

Write-Host ""

# Check Terraform configuration files
Write-ColorText "2. Configuration Files" "Blue"

$RequiredFiles = @("main.tf", "variables.tf", "outputs.tf", "s3.tf", "iam.tf", "route53.tf", "versions.tf")
foreach ($File in $RequiredFiles) {
    if (Test-Path $File) {
        Write-Status "OK" "$File exists"
    } else {
        Write-Status "ERROR" "$File missing"
    }
}

# Check for terraform.tfvars
if (Test-Path $TerraformVarFile) {
    Write-Status "OK" "terraform.tfvars exists"
} else {
    Write-Status "WARN" "terraform.tfvars not found (using defaults)"
}

Write-Host ""

# Terraform validation
Write-ColorText "3. Terraform Validation" "Blue"

# Initialize if needed
if (-not (Test-Path ".terraform")) {
    Write-Host "Initializing Terraform..."
    terraform init -backend=false >$null 2>&1
}

# Format check
Write-Host "Checking formatting..."
$FormatCheck = terraform fmt -check 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Status "OK" "Code formatting is correct"
} else {
    Write-Status "WARN" "Code needs formatting (run: terraform fmt)"
}

# Validate configuration
Write-Host "Validating configuration..."
$ValidateResult = terraform validate 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Status "OK" "Configuration is valid"
} else {
    Write-Status "ERROR" "Configuration validation failed"
    terraform validate
    exit 1
}

# Plan check (if variables exist)
if (Test-Path $TerraformVarFile) {
    Write-Host "Running terraform plan..."
    $PlanResult = terraform plan -var-file="terraform.tfvars" -out=validation.tfplan 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Status "OK" "Plan generation successful"
        
        # Clean up plan file
        Remove-Item "validation.tfplan" -ErrorAction SilentlyContinue
    } else {
        Write-Status "ERROR" "Plan generation failed"
        terraform plan -var-file="terraform.tfvars"
        exit 1
    }
} else {
    Write-Status "WARN" "Skipping plan check (no terraform.tfvars)"
}

Write-Host ""

# Variable validation
Write-ColorText "4. Variable Validation" "Blue"

if (Test-Path $TerraformVarFile) {
    $RequiredVars = @("project_name", "env", "aws_region")
    foreach ($Var in $RequiredVars) {
        $Pattern = "^$Var\s*="
        $Match = Select-String -Path $TerraformVarFile -Pattern $Pattern
        if ($Match) {
            $Value = ($Match.Line -split '=')[1].Trim(' "')
            Write-Status "OK" "$Var = $Value"
        } else {
            Write-Status "ERROR" "$Var not defined in terraform.tfvars"
        }
    }
    
    $OptionalVars = @("domain", "lb_dns", "route53_zone_id", "create_route53_record")
    foreach ($Var in $OptionalVars) {
        $Pattern = "^$Var\s*="
        $Match = Select-String -Path $TerraformVarFile -Pattern $Pattern
        if ($Match) {
            $Value = ($Match.Line -split '=')[1].Trim(' "')
            Write-Status "OK" "$Var = $Value (optional)"
        }
    }
} else {
    Write-Status "WARN" "No terraform.tfvars file to validate"
}

Write-Host ""

# Security validation
Write-ColorText "5. Security Validation" "Blue"

# Check for hardcoded secrets
$SecretFiles = Get-ChildItem -Recurse -Include "*.tf" | Where-Object { $_.Name -notlike "*example*" -and $_.Name -notlike "*template*" }
$HardcodedSecrets = $SecretFiles | Select-String -Pattern "AKIA|aws_access_key|aws_secret_key" 2>$null
if ($HardcodedSecrets) {
    Write-Status "ERROR" "Hardcoded AWS credentials found in configuration"
} else {
    Write-Status "OK" "No hardcoded AWS credentials found"
}

# Check for proper tagging
$TaggingCheck1 = Select-String -Path "*.tf" -Pattern "Environment.*var\.env" 2>$null
$TaggingCheck2 = Select-String -Path "*.tf" -Pattern "Project.*var\.project_name" 2>$null
if ($TaggingCheck1 -and $TaggingCheck2) {
    Write-Status "OK" "Resource tagging configured properly"
} else {
    Write-Status "WARN" "Resource tagging may be incomplete"
}

# Check S3 bucket security
$S3SecurityCheck1 = Select-String -Path "s3.tf" -Pattern "block_public_acls.*true" 2>$null
$S3SecurityCheck2 = Select-String -Path "s3.tf" -Pattern "server_side_encryption" 2>$null
if ($S3SecurityCheck1 -and $S3SecurityCheck2) {
    Write-Status "OK" "S3 security settings configured"
} else {
    Write-Status "ERROR" "S3 security settings missing"
}

Write-Host ""

# Summary
Write-ColorText "6. Validation Summary" "Blue"
Write-Host "Infrastructure validation completed."
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. If validation passed: terraform apply -var-file=`"terraform.tfvars`""
Write-Host "2. If issues found: Review and fix the reported problems"
Write-Host "3. For production: Set up remote state backend"
Write-Host ""
Write-Host "Documentation: README.md" 