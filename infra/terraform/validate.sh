#!/bin/bash
# Terraform validation script for Clip Downloader infrastructure

set -e

echo "🔍 Validating Terraform configuration..."

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform is not installed. Please install Terraform >= 1.6"
    echo "   Download from: https://www.terraform.io/downloads.html"
    exit 1
fi

# Check terraform version
TF_VERSION=$(terraform version -json | jq -r '.terraform_version')
echo "✅ Terraform version: $TF_VERSION"

# Format check
echo "🎨 Checking formatting..."
if terraform fmt -check -recursive; then
    echo "✅ Terraform formatting is correct"
else
    echo "❌ Terraform formatting issues found. Run 'terraform fmt -recursive' to fix."
    exit 1
fi

# Initialize (without backend)
echo "⚙️  Initializing Terraform..."
terraform init -backend=false

# Validate configuration
echo "🔎 Validating configuration..."
if terraform validate; then
    echo "✅ Terraform configuration is valid"
else
    echo "❌ Terraform validation failed"
    exit 1
fi

# Check for example variables file
if [ ! -f "terraform.tfvars.example" ]; then
    echo "❌ terraform.tfvars.example not found"
    exit 1
fi

echo "✅ All validation checks passed!"
echo ""
echo "Next steps:"
echo "1. Copy terraform.tfvars.example to terraform.tfvars"
echo "2. Update terraform.tfvars with your VPC and subnet IDs"
echo "3. Run 'terraform plan' to review the infrastructure"
echo "4. Run 'terraform apply' to create the infrastructure" 